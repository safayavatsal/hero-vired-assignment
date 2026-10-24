import json

import pytest
from fastapi.testclient import TestClient

from app import main
from app.main import PaymentRequest, PaymentService


class AlertGateway:
    def __init__(self) -> None:
        self.payload = None

    def create_incident(self, payload):
        self.payload = payload
        return "incident-1"


def payment(card_number: str) -> PaymentRequest:
    return PaymentRequest(
        attempt_id="attempt-1234",
        product_ids=["desk-lamp"],
        cardholder="Demo Shopper",
        card_number=card_number,
        expiry="12/30",
        security_code="123",
    )


def test_approved_payment_does_not_create_an_incident() -> None:
    gateway = AlertGateway()

    result = PaymentService(gateway).pay(payment("4242424242424242"))

    assert result == {"status": "approved", "order_id": "order-attempt-1234", "total_cents": 7900}
    assert gateway.payload is None


def test_declined_payment_creates_privacy_bounded_incident() -> None:
    gateway = AlertGateway()

    result = PaymentService(gateway).pay(payment("4111111111110002"))

    assert result == {"status": "declined", "incident_id": "incident-1", "total_cents": 7900}
    assert gateway.payload["service"] == "checkout-api"
    assert gateway.payload["source_event_id"] == "demo-payment-attempt-1234"
    assert gateway.payload["correlation_key"].endswith("attempt-1234")
    serialized = json.dumps(gateway.payload)
    assert "4111111111110002" not in serialized
    assert "Demo Shopper" not in serialized
    assert "security_code" not in serialized


def test_payment_rejects_unknown_products_before_alerting() -> None:
    gateway = AlertGateway()
    request = payment("4111111111110002").model_copy(update={"product_ids": ["unknown"]})

    with pytest.raises(ValueError, match="unknown product"):
        PaymentService(gateway).pay(request)

    assert gateway.payload is None


def test_payment_rejects_unlisted_test_cards() -> None:
    gateway = AlertGateway()

    with pytest.raises(ValueError, match="displayed synthetic card"):
        PaymentService(gateway).pay(payment("4000000000000000"))

    assert gateway.payload is None


def test_catalog_endpoint_returns_store_products() -> None:
    response = TestClient(main.app).get("/api/store/products")

    assert response.status_code == 200
    assert [product["id"] for product in response.json()] == ["desk-lamp", "travel-mug", "cable-kit"]


def test_payment_endpoint_returns_created_incident(monkeypatch) -> None:
    gateway = AlertGateway()
    monkeypatch.setattr(main, "payment_service", PaymentService(gateway))

    response = TestClient(main.app).post("/api/store/payments", json=payment("4111111111110002").model_dump())

    assert response.status_code == 200
    assert response.json()["incident_id"] == "incident-1"

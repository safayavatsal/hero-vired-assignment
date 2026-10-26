import json

import pytest
from fastapi.testclient import TestClient

from app import main
from app import observer as observer_module
from app.main import CustomerScenarioRequest, PaymentRequest, PaymentService
from app.observer import CheckoutObserver
from app.request_context import reset_request_id, set_request_id


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

    result = PaymentService(CheckoutObserver(gateway)).pay(payment("4242424242424242"))

    assert result == {"status": "approved", "order_id": "order-attempt-1234", "total_cents": 7900}
    assert gateway.payload is None


def test_declined_payment_creates_privacy_bounded_incident() -> None:
    gateway = AlertGateway()

    result = PaymentService(CheckoutObserver(gateway)).pay(payment("4111111111110002"))

    assert result == {
        "status": "declined",
        "payment_reference": "payment-attempt-1234",
        "incident_id": "incident-1",
        "observation_status": "delivered",
        "total_cents": 7900,
    }
    assert gateway.payload["service"] == "checkout-api"
    assert gateway.payload["source_event_id"] == "demo-payment-attempt-1234"
    assert gateway.payload["correlation_key"].endswith("attempt-1234")
    assert gateway.payload["labels"]["event_name"] == "checkout.authorization.failed"
    serialized = json.dumps(gateway.payload)
    assert "4111111111110002" not in serialized
    assert "Demo Shopper" not in serialized
    assert "security_code" not in serialized


def test_payment_rejects_unknown_products_before_alerting() -> None:
    gateway = AlertGateway()
    request = payment("4111111111110002").model_copy(update={"product_ids": ["unknown"]})

    with pytest.raises(ValueError, match="unknown product"):
        PaymentService(CheckoutObserver(gateway)).pay(request)

    assert gateway.payload is None


def test_payment_rejects_unlisted_test_cards() -> None:
    gateway = AlertGateway()

    with pytest.raises(ValueError, match="displayed synthetic card"):
        PaymentService(CheckoutObserver(gateway)).pay(payment("4000000000000000"))

    assert gateway.payload is None


def test_catalog_endpoint_returns_store_products() -> None:
    response = TestClient(main.app).get("/api/store/products")

    assert response.status_code == 200
    assert [product["id"] for product in response.json()] == ["desk-lamp", "travel-mug", "cable-kit"]


def test_store_returns_and_propagates_request_id(monkeypatch) -> None:
    response = TestClient(main.app).get("/api/store/health", headers={"X-Request-ID": "store-check-1"})
    assert response.headers["X-Request-ID"] == "store-check-1"

    captured = {}
    token = set_request_id("store-check-1")

    class Response:
        def read(self):
            return b'{"incident":{"id":"incident-1"}}'

        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return False

    def request(request, timeout):
        captured["request_id"] = request.get_header("X-request-id")
        return Response()

    try:
        monkeypatch.setattr(observer_module, "urlopen", request)
        observer_module.AlertGateway().create_incident({"source_event_id": "event-1"})
    finally:
        reset_request_id(token)

    assert captured == {"request_id": "store-check-1"}


def test_payment_endpoint_returns_created_incident(monkeypatch) -> None:
    gateway = AlertGateway()
    monkeypatch.setattr(main, "payment_service", PaymentService(CheckoutObserver(gateway)))

    response = TestClient(main.app).post("/api/store/payments", json=payment("4111111111110002").model_dump())

    assert response.status_code == 200
    assert response.json()["incident_id"] == "incident-1"


def test_payment_stays_failed_when_observation_delivery_is_unavailable() -> None:
    class UnavailableGateway:
        def create_incident(self, _payload):
            raise RuntimeError("observer unavailable")

    result = PaymentService(CheckoutObserver(UnavailableGateway())).pay(payment("4111111111110002"))

    assert result["status"] == "declined"
    assert result["incident_id"] is None
    assert result["observation_status"] == "unavailable"


@pytest.mark.parametrize(
    ("scenario_id", "expected_status", "expected_service", "expected_alert_type"),
    [
        ("deployment_regression", "degraded", "payments-api", "p99_latency_high"),
        ("disk_pressure", "delayed", "orders-worker", "disk_usage_high"),
        ("third_party_outage", "declined", "checkout-api", "dependency_errors_high"),
    ],
)
def test_customer_scenario_emits_canonical_alert_without_card_data(
    scenario_id: str, expected_status: str, expected_service: str, expected_alert_type: str
) -> None:
    gateway = AlertGateway()

    result = PaymentService(CheckoutObserver(gateway)).trigger_customer_scenario(
        scenario_id, CustomerScenarioRequest(attempt_id="scenario-1234", product_ids=["desk-lamp"])
    )

    assert result["status"] == expected_status
    assert result["incident_id"] == "incident-1"
    assert gateway.payload["service"] == expected_service
    assert gateway.payload["alert_type"] == expected_alert_type
    assert gateway.payload["labels"]["scenario"] == scenario_id
    assert "card_number" not in json.dumps(gateway.payload)


def test_customer_scenario_endpoint_rejects_unknown_scenario(monkeypatch) -> None:
    gateway = AlertGateway()
    monkeypatch.setattr(main, "payment_service", PaymentService(CheckoutObserver(gateway)))

    response = TestClient(main.app).post(
        "/api/store/scenarios/not-a-scenario",
        json={"attempt_id": "scenario-1234", "product_ids": ["desk-lamp"]},
    )

    assert response.status_code == 422
    assert gateway.payload is None

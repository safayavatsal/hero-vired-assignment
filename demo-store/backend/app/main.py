import json
import os
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field


@dataclass(frozen=True)
class Product:
    id: str
    name: str
    description: str
    price_cents: int
    tone: str


PRODUCTS = {
    product.id: product
    for product in (
        Product("desk-lamp", "Focus desk lamp", "Warm light with a low-glare work mode.", 7900, "amber"),
        Product("travel-mug", "Transit mug", "A leak-resistant mug for long workdays.", 3400, "blue"),
        Product("cable-kit", "Everyday cable kit", "Three durable charging cables in one pouch.", 2600, "green"),
    )
}


class PaymentRequest(BaseModel):
    attempt_id: str = Field(min_length=8, max_length=100, pattern=r"^[A-Za-z0-9-]+$")
    product_ids: list[str] = Field(min_length=1, max_length=20)
    cardholder: str = Field(min_length=1, max_length=100)
    card_number: str = Field(pattern=r"^\d{12,19}$")
    expiry: str = Field(pattern=r"^\d{2}/\d{2}$")
    security_code: str = Field(pattern=r"^\d{3,4}$")


class AlertGateway:
    def create_incident(self, payload: dict[str, Any]) -> str:
        base_url = os.getenv("ON_CALL_API_URL", "http://api:8000").rstrip("/")
        request = Request(
            f"{base_url}/api/v1/alerts",
            data=json.dumps(payload).encode(),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urlopen(request, timeout=5) as response:
                body = json.loads(response.read().decode())
        except (HTTPError, URLError, TimeoutError, ValueError) as error:
            raise RuntimeError("the on-call assistant did not accept the alert") from error
        incident_id = body.get("incident", {}).get("id")
        if not isinstance(incident_id, str) or not incident_id:
            raise RuntimeError("the on-call assistant returned an invalid incident")
        return incident_id


class PaymentService:
    def __init__(self, alert_gateway: AlertGateway | None = None) -> None:
        self.alert_gateway = alert_gateway or AlertGateway()

    def pay(self, payment: PaymentRequest) -> dict[str, Any]:
        products = [PRODUCTS.get(product_id) for product_id in payment.product_ids]
        if any(product is None for product in products):
            raise ValueError("the cart contains an unknown product")
        total_cents = sum(product.price_cents for product in products if product)
        if payment.card_number == "4242424242424242":
            return {"status": "approved", "order_id": f"order-{payment.attempt_id}", "total_cents": total_cents}
        if payment.card_number != "4111111111110002":
            raise ValueError("use one of the displayed synthetic card numbers")
        incident_id = self.alert_gateway.create_incident({
            "source_event_id": f"demo-payment-{payment.attempt_id}",
            "source": "demo-storefront",
            "service": "checkout-api",
            "severity": "critical",
            "alert_type": "payment_authorization_failed",
            "labels": {
                "scenario": "third_party_outage",
                "failure_category": "authorization_unavailable",
                "product_ids": ",".join(payment.product_ids),
                "order_total_cents": str(total_cents),
            },
            "description": "Checkout payment authorization is unavailable for a synthetic order.",
            "lifecycle": "firing",
            "source_time": datetime.now(timezone.utc).isoformat(),
            "correlation_key": f"checkout-authorization-provider-{payment.attempt_id}",
        })
        return {"status": "declined", "incident_id": incident_id, "total_cents": total_cents}


app = FastAPI(title="Northstar Supply Demo Store")
payment_service = PaymentService()


@app.get("/api/store/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/api/store/products")
def list_products() -> list[dict[str, Any]]:
    return [asdict(product) for product in PRODUCTS.values()]


@app.post("/api/store/payments")
def create_payment(payment: PaymentRequest) -> dict[str, Any]:
    try:
        return payment_service.pay(payment)
    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error
    except RuntimeError as error:
        raise HTTPException(status_code=502, detail=str(error)) from error

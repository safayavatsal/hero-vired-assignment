from dataclasses import asdict, dataclass
from typing import Any

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from app.observer import CheckoutObserver


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


class CustomerScenarioRequest(BaseModel):
    attempt_id: str = Field(min_length=8, max_length=100, pattern=r"^[A-Za-z0-9-]+$")
    product_ids: list[str] = Field(min_length=1, max_length=20)


class PaymentService:
    def __init__(self, observer: CheckoutObserver | None = None) -> None:
        self.observer = observer or CheckoutObserver()

    def pay(self, payment: PaymentRequest) -> dict[str, Any]:
        products = [PRODUCTS.get(product_id) for product_id in payment.product_ids]
        if any(product is None for product in products):
            raise ValueError("the cart contains an unknown product")
        total_cents = sum(product.price_cents for product in products if product)
        if payment.card_number == "4242424242424242":
            return {"status": "approved", "order_id": f"order-{payment.attempt_id}", "total_cents": total_cents}
        if payment.card_number != "4111111111110002":
            raise ValueError("use one of the displayed synthetic card numbers")
        incident_id = self.observer.record_authorization_unavailable(payment.attempt_id, payment.product_ids, total_cents)
        return {
            "status": "declined",
            "payment_reference": f"payment-{payment.attempt_id}",
            "incident_id": incident_id,
            "observation_status": "delivered" if incident_id else "unavailable",
            "total_cents": total_cents,
        }

    def trigger_customer_scenario(self, scenario_id: str, request: CustomerScenarioRequest) -> dict[str, Any]:
        products = [PRODUCTS.get(product_id) for product_id in request.product_ids]
        if any(product is None for product in products):
            raise ValueError("the cart contains an unknown product")
        total_cents = sum(product.price_cents for product in products if product)
        incident_id = self.observer.record_customer_scenario(
            scenario_id, request.attempt_id, request.product_ids, total_cents
        )
        messages = {
            "deployment_regression": ("degraded", "Checkout is taking longer than usual. Please try again shortly."),
            "disk_pressure": ("delayed", "Your order is accepted, but fulfillment is temporarily delayed."),
            "third_party_outage": ("declined", "Your card provider is temporarily unavailable. Please try again shortly."),
        }
        if scenario_id not in messages:
            raise ValueError("unknown customer scenario")
        status, customer_message = messages[scenario_id]
        return {
            "status": status,
            "customer_message": customer_message,
            "reference": f"demo-{scenario_id}-{request.attempt_id}",
            "incident_id": incident_id,
            "observation_status": "delivered" if incident_id else "unavailable",
            "total_cents": total_cents,
        }


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


@app.post("/api/store/scenarios/{scenario_id}")
def trigger_customer_scenario(scenario_id: str, request: CustomerScenarioRequest) -> dict[str, Any]:
    try:
        return payment_service.trigger_customer_scenario(scenario_id, request)
    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error

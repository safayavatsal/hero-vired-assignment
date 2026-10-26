import json
import os
from datetime import datetime, timezone
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen
from app.request_context import current_request_id


class AlertGateway:
    def create_incident(self, payload: dict[str, Any]) -> str:
        base_url = os.getenv("ON_CALL_API_URL", "http://api:8000").rstrip("/")
        request = Request(
            f"{base_url}/api/v1/alerts",
            data=json.dumps(payload).encode(),
            headers={"Content-Type": "application/json", **({"X-Request-ID": current_request_id()} if current_request_id() else {})},
            method="POST",
        )
        try:
            with urlopen(request, timeout=5) as response:
                body = json.loads(response.read().decode())
        except (HTTPError, URLError, TimeoutError, ValueError) as error:
            raise RuntimeError("the observer could not deliver the event") from error
        incident_id = body.get("incident", {}).get("id")
        if not isinstance(incident_id, str) or not incident_id:
            raise RuntimeError("the observer received an invalid event receipt")
        return incident_id


class CheckoutObserver:
    def __init__(self, alert_gateway: AlertGateway | None = None) -> None:
        self.alert_gateway = alert_gateway or AlertGateway()

    def record_authorization_unavailable(self, attempt_id: str, product_ids: list[str], total_cents: int) -> str | None:
        try:
            return self.alert_gateway.create_incident({
                "source_event_id": f"demo-payment-{attempt_id}",
                "source": "demo-store-observer",
                "service": "checkout-api",
                "severity": "critical",
                "alert_type": "payment_authorization_failed",
                "labels": {
                    "event_name": "checkout.authorization.failed",
                    "scenario": "third_party_outage",
                    "failure_category": "authorization_unavailable",
                    "product_ids": ",".join(product_ids),
                    "order_total_cents": str(total_cents),
                },
                "description": "Checkout authorization dependency is unavailable.",
                "lifecycle": "firing",
                "source_time": datetime.now(timezone.utc).isoformat(),
                "correlation_key": f"checkout-authorization-provider-{attempt_id}",
            })
        except RuntimeError:
            return None

    def record_customer_scenario(self, scenario_id: str, attempt_id: str, product_ids: list[str], total_cents: int) -> str | None:
        scenarios = {
            "deployment_regression": {
                "service": "payments-api",
                "severity": "critical",
                "alert_type": "p99_latency_high",
                "event_name": "checkout.latency.regression",
                "failure_category": "deployment_regression",
                "description": "Checkout latency increased after a payment service release.",
            },
            "disk_pressure": {
                "service": "orders-worker",
                "severity": "high",
                "alert_type": "disk_usage_high",
                "event_name": "fulfillment.disk.pressure",
                "failure_category": "disk_pressure",
                "description": "Order fulfillment is delayed while the warehouse worker recovers.",
            },
            "third_party_outage": {
                "service": "checkout-api",
                "severity": "critical",
                "alert_type": "dependency_errors_high",
                "event_name": "checkout.authorization.failed",
                "failure_category": "authorization_unavailable",
                "description": "Checkout authorization dependency is unavailable.",
            },
        }
        scenario = scenarios.get(scenario_id)
        if scenario is None:
            raise ValueError("unknown customer scenario")
        try:
            return self.alert_gateway.create_incident({
                "source_event_id": f"demo-scenario-{scenario_id}-{attempt_id}",
                "source": "demo-store-observer",
                "service": scenario["service"],
                "severity": scenario["severity"],
                "alert_type": scenario["alert_type"],
                "labels": {
                    "event_name": scenario["event_name"],
                    "scenario": scenario_id,
                    "failure_category": scenario["failure_category"],
                    "product_ids": ",".join(product_ids),
                    "order_total_cents": str(total_cents),
                },
                "description": scenario["description"],
                "lifecycle": "firing",
                "source_time": datetime.now(timezone.utc).isoformat(),
                "correlation_key": f"demo-store-{scenario_id}-{attempt_id}",
            })
        except RuntimeError:
            return None

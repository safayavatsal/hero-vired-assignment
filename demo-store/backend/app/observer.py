import json
import os
from datetime import datetime, timezone
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


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

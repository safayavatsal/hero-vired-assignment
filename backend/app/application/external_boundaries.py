import json
import os
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from app.application.resilience import env_float


class ExternalBoundaryError(ValueError):
    pass


def _request_json(url: str, token: str, payload: dict[str, Any]) -> dict[str, Any]:
    request = Request(url, data=json.dumps(payload).encode(), method="POST")
    request.add_header("Content-Type", "application/json")
    if token:
        request.add_header("Authorization", f"Bearer {token}")
    try:
        with urlopen(request, timeout=env_float("EXTERNAL_BOUNDARY_TIMEOUT_SECONDS", 5.0, 0.1, 30.0)) as response:
            body = json.loads(response.read().decode())
    except (HTTPError, URLError, TimeoutError, ValueError) as error:
        raise ExternalBoundaryError("external boundary request failed") from error
    if not isinstance(body, dict):
        raise ExternalBoundaryError("external boundary returned an invalid response")
    return body


class OwnershipGateway:
    def resolve(self, service: str, severity: str) -> dict[str, str] | None:
        url = os.getenv("OWNERSHIP_GATEWAY_URL")
        if not url:
            return None
        result = _request_json(url, os.getenv("OWNERSHIP_GATEWAY_TOKEN", ""), {"service": service, "severity": severity})
        primary = result.get("responder") or result.get("primary_responder")
        fallback = result.get("fallback_responder")
        if not isinstance(primary, str) or not isinstance(fallback, str) or not primary or not fallback:
            raise ExternalBoundaryError("ownership response must include responder and fallback_responder")
        return {"responder": primary, "fallback_responder": fallback}


class NotificationGateway:
    def deliver(self, payload: dict[str, Any]) -> dict[str, Any] | None:
        url = os.getenv("NOTIFICATION_GATEWAY_URL")
        if not url:
            return None
        result = _request_json(url, os.getenv("NOTIFICATION_GATEWAY_TOKEN", ""), payload)
        if result.get("status") not in {None, "accepted", "delivered"}:
            raise ExternalBoundaryError("notification delivery was rejected")
        return result


class ActionExecutorGateway:
    def reconcile(self, action: dict[str, Any]) -> dict[str, Any] | None:
        url = os.getenv("ACTION_EXECUTOR_URL")
        if not url:
            return None
        return _request_json(
            url,
            os.getenv("ACTION_EXECUTOR_TOKEN", ""),
            {"action_id": str(action["id"]), "idempotency_key": action["idempotency_key"], "target": action["target"]},
        )

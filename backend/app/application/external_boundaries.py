import json
import os
import smtplib
from email.message import EmailMessage
from email.utils import make_msgid
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
        ownership = {"responder": primary, "fallback_responder": fallback}
        for key in ("responder_email", "fallback_email"):
            value = result.get(key)
            if isinstance(value, str) and value:
                ownership[key] = value
        return ownership


class NotificationGateway:
    def deliver(self, payload: dict[str, Any]) -> dict[str, Any] | None:
        url = os.getenv("NOTIFICATION_GATEWAY_URL")
        if url:
            result = _request_json(url, os.getenv("NOTIFICATION_GATEWAY_TOKEN", ""), payload)
            if result.get("status") not in {None, "accepted", "delivered"}:
                raise ExternalBoundaryError("notification delivery was rejected")
            return result
        host = os.getenv("NOTIFICATION_SMTP_HOST")
        if not host:
            return None
        message = EmailMessage()
        incident_id = str(payload.get("incident_id", ""))
        severity = str(payload.get("severity", "incident")).replace("\r", " ").replace("\n", " ")
        service = str(payload.get("service", "service")).replace("\r", " ").replace("\n", " ")
        responder = str(payload.get("responder", "service-owner")).replace("\r", " ").replace("\n", " ")
        recipient = payload.get("responder_email") or os.getenv("NOTIFICATION_EMAIL_TO") or f"{responder}@{os.getenv('NOTIFICATION_EMAIL_DOMAIN', 'demo.local')}"
        console_url = os.getenv("INCIDENT_CONSOLE_URL", "http://localhost:8000/?incident={incident_id}").format(incident_id=incident_id)
        response_channel_url = os.getenv("RESPONSE_CHANNEL_URL", "http://localhost:8002")
        message["Subject"] = f"[{severity.upper()}] {service} needs attention"
        message["From"] = os.getenv("NOTIFICATION_EMAIL_FROM", "assistant@demo.local")
        message["To"] = recipient
        message["Message-ID"] = make_msgid(domain="demo.local")
        lines = [
            f"Incident ID: {incident_id}",
            f"Service: {service}",
            f"Summary: {payload.get('summary', '')}",
            f"Owner: {responder}",
            f"Finding: {payload.get('evidence_summary', 'Investigation pending')}",
            f"Likely cause: {payload.get('likely_cause', 'See the investigation evidence')}",
            f"Suggested next step: {payload.get('suggested_next_step', 'Review incident')}",
            "",
            "Evidence:",
        ]
        for evidence in payload.get("evidence", []):
            lines.append(f"- {evidence.get('source_type', 'source')}: {json.dumps(evidence.get('items', []), sort_keys=True)}")
        lines.extend([
            "",
            f"Open incident console: {console_url}",
            f"Open responder inbox: {response_channel_url}",
        ])
        message.set_content("\n".join(lines))
        try:
            with smtplib.SMTP(
                host,
                int(os.getenv("NOTIFICATION_SMTP_PORT", "1025")),
                timeout=env_float("EXTERNAL_BOUNDARY_TIMEOUT_SECONDS", 5.0, 0.1, 30.0),
            ) as smtp:
                smtp.send_message(message)
        except (OSError, smtplib.SMTPException, ValueError) as error:
            raise ExternalBoundaryError("notification email delivery failed") from error
        return {"status": "delivered", "id": message["Message-ID"]}


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

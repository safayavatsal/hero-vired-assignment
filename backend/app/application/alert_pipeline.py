import hashlib
import json
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from app.domain.incident import Alert
from app.ports.incident_repository import IncidentRepository


class AlertPipelineService:
    def __init__(self, repository: IncidentRepository) -> None:
        self.repository = repository

    def initialize(self) -> None:
        self.repository.initialize()

    def accept(self, payload: dict[str, Any]) -> dict[str, Any]:
        received_time = datetime.now(timezone.utc)
        return self.repository.accept_alert(self._normalize(payload, received_time))

    def list_incidents(self) -> list[dict[str, Any]]:
        return self.repository.list_incidents()

    def get_incident(self, incident_id):
        incident = self.repository.get_incident(incident_id)
        if incident is None:
            raise ValueError("incident not found")
        return incident

    def get_timeline(self, incident_id):
        timeline = self.repository.get_timeline(incident_id)
        if timeline is None:
            raise ValueError("incident not found")
        return timeline

    def transition(self, incident_id, target_status: str, expected_version: int | None) -> dict[str, Any]:
        return self.repository.transition(incident_id, target_status, expected_version)

    def _normalize(self, payload: dict[str, Any], received_time: datetime) -> Alert:
        source = str(payload["source"]).strip()
        service = str(payload["service"]).strip()
        alert_type = str(payload["alert_type"]).strip()
        labels = {str(key): str(value) for key, value in payload.get("labels", {}).items()}
        source_time = payload["source_time"]
        if isinstance(source_time, str):
            source_time = datetime.fromisoformat(source_time.replace("Z", "+00:00"))
        if source_time.tzinfo is None:
            source_time = source_time.replace(tzinfo=timezone.utc)
        return Alert(
            id=uuid4(),
            source_event_id=str(payload["source_event_id"]),
            fingerprint=self._fingerprint(source, service, alert_type, labels, payload.get("correlation_key")),
            source=source,
            service=service,
            severity=str(payload["severity"]).strip(),
            alert_type=alert_type,
            labels=labels,
            description=str(payload.get("description", "")),
            lifecycle=str(payload.get("lifecycle", "firing")),
            source_time=source_time,
            received_time=received_time,
            raw_payload=payload,
        )

    @staticmethod
    def _fingerprint(source: str, service: str, alert_type: str, labels: dict[str, str], correlation_key: Any) -> str:
        value = {
            "source": source,
            "service": service,
            "alert_type": alert_type,
            "labels": labels,
            "correlation_key": correlation_key,
        }
        encoded = json.dumps(value, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(encoded.encode("utf-8")).hexdigest()

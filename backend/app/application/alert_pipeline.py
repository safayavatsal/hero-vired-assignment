import hashlib
import json
from datetime import datetime, timezone
from typing import Any
from uuid import UUID, uuid4

from app.domain.incident import Alert, Incident, TimelineEvent


class AlertPipelineService:
    def __init__(self) -> None:
        self._incidents: dict[UUID, Incident] = {}
        self._incidents_by_fingerprint: dict[str, UUID] = {}
        self._alerts_by_source_event: dict[str, Alert] = {}

    def reset(self) -> None:
        self._incidents.clear()
        self._incidents_by_fingerprint.clear()
        self._alerts_by_source_event.clear()

    def accept(self, payload: dict[str, Any]) -> dict[str, Any]:
        received_time = datetime.now(timezone.utc)
        alert = self._normalize(payload, received_time)
        duplicate = alert.source_event_id in self._alerts_by_source_event
        if duplicate:
            existing = self._alerts_by_source_event[alert.source_event_id]
            incident = self._incidents[existing.incident_id]
            return self._response(incident, existing, True)

        incident = self._find_or_create_incident(alert)
        alert.incident_id = incident.id
        self._alerts_by_source_event[alert.source_event_id] = alert
        incident.alerts.append(alert)
        incident.updated_at = received_time
        if alert.lifecycle == "resolved":
            incident.status = "resolved"
        elif incident.status == "resolved":
            incident.status = "received"

        self._append_timeline(incident, alert)
        return self._response(incident, alert, False)

    def list_incidents(self) -> list[dict[str, Any]]:
        incidents = sorted(
            self._incidents.values(),
            key=lambda incident: incident.updated_at,
            reverse=True,
        )
        return [self._incident_summary(incident) for incident in incidents]

    def get_incident(self, incident_id: UUID) -> dict[str, Any]:
        incident = self._incidents.get(incident_id)
        if incident is None:
            raise ValueError("incident not found")
        return self._serialize_incident(incident)

    def get_timeline(self, incident_id: UUID) -> list[dict[str, Any]]:
        incident = self._incidents.get(incident_id)
        if incident is None:
            raise ValueError("incident not found")
        ordered = sorted(
            incident.timeline,
            key=lambda event: (event.event_time, event.received_time, event.sequence_number),
        )
        return [self._serialize_timeline_event(event) for event in ordered]

    def _normalize(self, payload: dict[str, Any], received_time: datetime) -> Alert:
        source = str(payload["source"]).strip()
        service = str(payload["service"]).strip()
        alert_type = str(payload["alert_type"]).strip()
        labels = {str(key): str(value) for key, value in payload.get("labels", {}).items()}
        fingerprint = self._fingerprint(source, service, alert_type, labels, payload.get("correlation_key"))
        source_time = payload["source_time"]
        if isinstance(source_time, str):
            source_time = datetime.fromisoformat(source_time.replace("Z", "+00:00"))
        if source_time.tzinfo is None:
            source_time = source_time.replace(tzinfo=timezone.utc)
        return Alert(
            id=uuid4(),
            source_event_id=str(payload["source_event_id"]),
            fingerprint=fingerprint,
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

    def _find_or_create_incident(self, alert: Alert) -> Incident:
        incident_id = self._incidents_by_fingerprint.get(alert.fingerprint)
        if incident_id is not None:
            return self._incidents[incident_id]
        incident = Incident(
            id=uuid4(),
            fingerprint=alert.fingerprint,
            service=alert.service,
            severity=alert.severity,
            status="received",
            summary=alert.description,
            created_at=alert.received_time,
            updated_at=alert.received_time,
        )
        self._incidents[incident.id] = incident
        self._incidents_by_fingerprint[alert.fingerprint] = incident.id
        return incident

    @staticmethod
    def _fingerprint(
        source: str,
        service: str,
        alert_type: str,
        labels: dict[str, str],
        correlation_key: Any,
    ) -> str:
        value = {
            "source": source,
            "service": service,
            "alert_type": alert_type,
            "labels": labels,
            "correlation_key": correlation_key,
        }
        encoded = json.dumps(value, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(encoded.encode("utf-8")).hexdigest()

    def _append_timeline(self, incident: Incident, alert: Alert) -> None:
        event = TimelineEvent(
            id=uuid4(),
            incident_id=incident.id,
            event_type="alert_received",
            event_time=alert.source_time,
            received_time=alert.received_time,
            sequence_number=len(incident.timeline) + 1,
            payload={
                "alert_id": str(alert.id),
                "source_event_id": alert.source_event_id,
                "fingerprint": alert.fingerprint,
                "lifecycle": alert.lifecycle,
                "raw_payload": alert.raw_payload,
            },
        )
        incident.timeline.append(event)

    def _response(self, incident: Incident, alert: Alert, duplicate: bool) -> dict[str, Any]:
        return {
            "duplicate": duplicate,
            "alert": self._serialize_alert(alert),
            "incident": self._incident_summary(incident),
        }

    @staticmethod
    def _incident_summary(incident: Incident) -> dict[str, Any]:
        return {
            "id": str(incident.id),
            "fingerprint": incident.fingerprint,
            "service": incident.service,
            "severity": incident.severity,
            "status": incident.status,
            "summary": incident.summary,
            "alert_count": len(incident.alerts),
            "updated_at": incident.updated_at.isoformat(),
        }

    def _serialize_incident(self, incident: Incident) -> dict[str, Any]:
        return {
            **self._incident_summary(incident),
            "created_at": incident.created_at.isoformat(),
            "alerts": [self._serialize_alert(alert) for alert in incident.alerts],
            "timeline": self.get_timeline(incident.id),
        }

    @staticmethod
    def _serialize_alert(alert: Alert) -> dict[str, Any]:
        return {
            "id": str(alert.id),
            "incident_id": str(alert.incident_id),
            "source_event_id": alert.source_event_id,
            "fingerprint": alert.fingerprint,
            "source": alert.source,
            "service": alert.service,
            "severity": alert.severity,
            "alert_type": alert.alert_type,
            "labels": alert.labels,
            "description": alert.description,
            "lifecycle": alert.lifecycle,
            "source_time": alert.source_time.isoformat(),
            "received_time": alert.received_time.isoformat(),
            "raw_payload": alert.raw_payload,
        }

    @staticmethod
    def _serialize_timeline_event(event: TimelineEvent) -> dict[str, Any]:
        return {
            "id": str(event.id),
            "incident_id": str(event.incident_id),
            "event_type": event.event_type,
            "event_time": event.event_time.isoformat(),
            "received_time": event.received_time.isoformat(),
            "sequence_number": event.sequence_number,
            "payload": event.payload,
        }

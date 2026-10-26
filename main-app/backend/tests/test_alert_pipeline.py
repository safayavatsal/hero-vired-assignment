from datetime import datetime, timedelta, timezone
from uuid import UUID

from app.application.alert_pipeline import AlertPipelineService
from app.domain.incident import Alert


class FakeIncidentRepository:
    def __init__(self) -> None:
        self.alerts: dict[str, Alert] = {}
        self.incidents: dict[str, dict] = {}

    def initialize(self) -> None:
        return None

    def accept_alert(self, alert: Alert) -> dict:
        if alert.source_event_id in self.alerts:
            stored = self.alerts[alert.source_event_id]
            return {"duplicate": True, "alert": self._alert(stored), "incident": self.incidents[str(stored.incident_id)]}
        incident_id = next((key for key, value in self.incidents.items() if value["fingerprint"] == alert.fingerprint), None)
        if incident_id is None:
            incident_id = str(UUID(int=len(self.incidents) + 1))
            self.incidents[incident_id] = {
                "id": incident_id, "fingerprint": alert.fingerprint, "service": alert.service,
                "severity": alert.severity, "status": "received", "summary": alert.description,
                "alert_count": 0, "updated_at": alert.received_time.isoformat(), "alerts": [],
            }
        alert.incident_id = UUID(incident_id)
        self.alerts[alert.source_event_id] = alert
        incident = self.incidents[incident_id]
        incident["alert_count"] += 1
        incident["alerts"].append(alert)
        return {"duplicate": False, "alert": self._alert(alert), "incident": self._summary(incident)}

    def list_incidents(self) -> list[dict]:
        return [self._summary(incident) for incident in self.incidents.values()]

    def get_incident(self, incident_id: UUID) -> dict | None:
        incident = self.incidents.get(str(incident_id))
        if incident is None:
            return None
        return {**self._summary(incident), "alerts": [self._alert(alert) for alert in incident["alerts"]]}

    def get_timeline(self, incident_id: UUID) -> list[dict] | None:
        incident = self.incidents.get(str(incident_id))
        if incident is None:
            return None
        return [{"payload": {"source_event_id": alert.source_event_id}, "event_time": alert.source_time.isoformat()} for alert in sorted(incident["alerts"], key=lambda item: item.source_time)]

    def transition(self, incident_id: UUID, target_status: str, expected_version: int | None) -> dict:
        incident = self.incidents.get(str(incident_id))
        if incident is None:
            raise ValueError("incident not found")
        if target_status != "investigating":
            raise ValueError("invalid transition")
        incident["status"] = target_status
        return self._summary(incident)

    @staticmethod
    def _summary(incident: dict) -> dict:
        return {key: value for key, value in incident.items() if key not in {"alerts"}}

    @staticmethod
    def _alert(alert: Alert) -> dict:
        return {"id": str(alert.id), "incident_id": str(alert.incident_id), "source_event_id": alert.source_event_id}


def payload(source_event_id: str, source_time: datetime, lifecycle: str = "firing") -> dict:
    return {
        "source_event_id": source_event_id,
        "source": "simulator",
        "service": "payments-api",
        "severity": "critical",
        "alert_type": "p99_latency_high",
        "source_time": source_time,
        "labels": {"region": "primary"},
        "description": "p99 latency is above threshold",
        "lifecycle": lifecycle,
        "correlation_key": "payments-latency",
    }


def test_duplicate_alert_does_not_create_side_effects() -> None:
    service = AlertPipelineService(FakeIncidentRepository())
    now = datetime.now(timezone.utc)

    first = service.accept(payload("event-1", now))
    duplicate = service.accept(payload("event-1", now))

    assert first["duplicate"] is False
    assert duplicate["duplicate"] is True
    assert len(service.list_incidents()) == 1
    assert service.list_incidents()[0]["alert_count"] == 1


def test_correlated_alerts_share_incident_and_timeline_is_event_ordered() -> None:
    service = AlertPipelineService(FakeIncidentRepository())
    now = datetime.now(timezone.utc)

    first = service.accept(payload("event-1", now))
    service.accept(payload("event-2", now - timedelta(minutes=5)))

    incident_id = first["incident"]["id"]
    incident = service.get_incident(UUID(incident_id))
    timeline = service.get_timeline(UUID(incident_id))

    assert incident["alert_count"] == 2
    assert [event["payload"]["source_event_id"] for event in timeline] == ["event-2", "event-1"]


def test_incident_transition_is_delegated_to_repository() -> None:
    service = AlertPipelineService(FakeIncidentRepository())
    result = service.accept(payload("event-1", datetime.now(timezone.utc)))

    transitioned = service.transition(UUID(result["incident"]["id"]), "investigating", None)

    assert transitioned["status"] == "investigating"


def test_storefront_payment_failure_uses_canonical_deduplication() -> None:
    repository = FakeIncidentRepository()
    service = AlertPipelineService(repository)
    payment_failure = {
        "source_event_id": "payment-demo-1",
        "source": "demo-storefront",
        "service": "checkout-api",
        "severity": "critical",
        "alert_type": "payment_authorization_failed",
        "source_time": datetime.now(timezone.utc),
        "labels": {"failure_category": "authorization_unavailable", "product_ids": "desk-lamp"},
        "description": "Checkout payment authorization is unavailable for a synthetic order.",
        "lifecycle": "firing",
        "correlation_key": "checkout-authorization-provider-payment-demo-1",
    }

    first = service.accept(payment_failure)
    duplicate = service.accept(payment_failure)

    assert first["duplicate"] is False
    assert duplicate["duplicate"] is True
    assert first["incident"]["service"] == "checkout-api"
    assert repository.alerts["payment-demo-1"].raw_payload == payment_failure

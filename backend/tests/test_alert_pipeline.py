from datetime import datetime, timedelta, timezone
from uuid import UUID

from app.application.alert_pipeline import AlertPipelineService


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
    service = AlertPipelineService()
    now = datetime.now(timezone.utc)

    first = service.accept(payload("event-1", now))
    duplicate = service.accept(payload("event-1", now))

    assert first["duplicate"] is False
    assert duplicate["duplicate"] is True
    assert len(service.list_incidents()) == 1
    assert service.list_incidents()[0]["alert_count"] == 1


def test_correlated_alerts_share_incident_and_timeline_is_event_ordered() -> None:
    service = AlertPipelineService()
    now = datetime.now(timezone.utc)

    first = service.accept(payload("event-1", now))
    service.accept(payload("event-2", now - timedelta(minutes=5)))

    incident_id = first["incident"]["id"]
    incident = service.get_incident(UUID(incident_id))
    timeline = service.get_timeline(UUID(incident_id))

    assert incident["alert_count"] == 2
    assert [event["payload"]["source_event_id"] for event in timeline] == ["event-2", "event-1"]

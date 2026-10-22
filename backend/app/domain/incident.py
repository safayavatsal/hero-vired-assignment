from dataclasses import dataclass, field
from datetime import datetime
from typing import Any
from uuid import UUID


INCIDENT_TRANSITIONS = {
    "received": {"investigating", "escalated", "resolved", "unfixable", "failed"},
    "investigating": {"awaiting_human", "action_pending", "resolved", "unfixable", "failed"},
    "awaiting_human": {"investigating", "escalated", "action_pending", "resolved", "failed"},
    "escalated": {"awaiting_human", "action_pending", "resolved", "unfixable", "failed"},
    "action_pending": {"action_running", "awaiting_human", "failed"},
    "action_running": {"action_unknown", "resolved", "failed"},
    "action_unknown": {"action_running", "resolved", "failed"},
    "resolved": {"received"},
    "unfixable": {"received"},
    "failed": {"received"},
}


@dataclass
class Alert:
    id: UUID
    source_event_id: str
    fingerprint: str
    source: str
    service: str
    severity: str
    alert_type: str
    labels: dict[str, str]
    description: str
    lifecycle: str
    source_time: datetime
    received_time: datetime
    raw_payload: dict[str, Any]
    incident_id: UUID | None = None


@dataclass
class TimelineEvent:
    id: UUID
    incident_id: UUID
    event_type: str
    event_time: datetime
    received_time: datetime
    sequence_number: int
    payload: dict[str, Any]


@dataclass
class Incident:
    id: UUID
    fingerprint: str
    service: str
    severity: str
    status: str
    summary: str
    created_at: datetime
    updated_at: datetime
    alerts: list[Alert] = field(default_factory=list)
    timeline: list[TimelineEvent] = field(default_factory=list)

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any
from uuid import UUID


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

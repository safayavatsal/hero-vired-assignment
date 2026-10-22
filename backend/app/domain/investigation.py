from dataclasses import dataclass
from datetime import datetime
from typing import Any


@dataclass(frozen=True)
class Evidence:
    id: str
    source_type: str
    availability: str
    observed_at: datetime
    items: list[dict[str, Any]]


@dataclass(frozen=True)
class Finding:
    id: str
    category: str
    statement: str
    confidence: float
    suggested_next_step: str
    evidence_ids: list[str]
    uncertainty: str | None

from typing import Any, Protocol
from uuid import UUID


class InvestigationRepository(Protocol):
    def initialize(self) -> None: ...

    def save(self, result: dict[str, Any]) -> None: ...

    def get(self, incident_id: UUID) -> dict[str, Any] | None: ...

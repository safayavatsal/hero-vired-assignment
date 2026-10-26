from typing import Any, Protocol
from uuid import UUID


class JobQueue(Protocol):
    def claim(self, job_type: str | None = None) -> dict[str, Any] | None: ...

    def complete(self, job_id: UUID) -> None: ...

    def fail(self, job_id: UUID, error: str) -> None: ...

from typing import Any, Protocol


class RetrievalRepository(Protocol):
    def index(self, result: dict[str, Any]) -> None: ...

    def count(self) -> int: ...

    def search(
        self,
        query_embedding: list[float],
        limit: int,
        exclude_incident_id: str | None = None,
    ) -> list[dict[str, Any]]: ...

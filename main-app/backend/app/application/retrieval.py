import hashlib
import math
import re
from datetime import datetime, timezone
from typing import Any
from uuid import NAMESPACE_URL, uuid5


EMBEDDING_DIMENSIONS = 128
SIMILAR_INCIDENTS_SOURCE = "similar_incidents"


def embed_text(text: str) -> list[float]:
    vector = [0.0] * EMBEDDING_DIMENSIONS
    for token in re.findall(r"[a-z0-9]+", text.lower()):
        bucket = int(hashlib.md5(token.encode("utf-8")).hexdigest(), 16) % EMBEDDING_DIMENSIONS
        vector[bucket] += 1.0
    norm = math.sqrt(sum(value * value for value in vector))
    if norm == 0:
        return vector
    return [value / norm for value in vector]


def cosine_similarity(left: list[float], right: list[float]) -> float:
    if not left or not right or len(left) != len(right):
        return 0.0
    return sum(a * b for a, b in zip(left, right))


class InMemoryRetrievalRepository:
    def __init__(self) -> None:
        self.records: list[dict[str, Any]] = []

    def index(self, result: dict[str, Any]) -> None:
        incident_id = result["incident_id"]
        service = result.get("service")
        for finding in result.get("findings", []):
            record = {
                "id": str(uuid5(NAMESPACE_URL, f"{incident_id}:{finding['category']}")),
                "incident_id": incident_id,
                "service": service,
                "category": finding["category"],
                "statement": finding["statement"],
                "suggested_next_step": finding.get("suggested_next_step"),
                "embedding": embed_text(f"{service or ''} {finding['category']} {finding['statement']}"),
                "created_at": datetime.now(timezone.utc).isoformat(),
            }
            self.records = [existing for existing in self.records if existing["id"] != record["id"]]
            self.records.append(record)

    def count(self) -> int:
        return len({record["incident_id"] for record in self.records})

    def search(
        self,
        query_embedding: list[float],
        limit: int,
        exclude_incident_id: str | None = None,
    ) -> list[dict[str, Any]]:
        ranked = sorted(
            (record for record in self.records if record["incident_id"] != exclude_incident_id),
            key=lambda record: cosine_similarity(query_embedding, record["embedding"]),
            reverse=True,
        )
        return [
            {
                **{key: value for key, value in record.items() if key != "embedding"},
                "similarity": round(cosine_similarity(query_embedding, record["embedding"]), 4),
            }
            for record in ranked[: max(0, limit)]
        ]

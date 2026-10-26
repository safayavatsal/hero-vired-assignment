import os
from typing import Any
from uuid import NAMESPACE_URL, UUID, uuid5

import psycopg
from psycopg.rows import dict_row
from psycopg.types.json import Jsonb

from app.application.retrieval import cosine_similarity, embed_text


DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://postgres:postgres@localhost:5432/hero_vired",
)


class PostgresRetrievalRepository:
    def __init__(self, database_url: str = DATABASE_URL) -> None:
        self.database_url = database_url

    def index(self, result: dict[str, Any]) -> None:
        findings = result.get("findings") or []
        if not findings:
            return
        service = result.get("service")
        with psycopg.connect(self.database_url, row_factory=dict_row) as connection:
            for finding in findings:
                embedding = embed_text(f"{service or ''} {finding['category']} {finding['statement']}")
                connection.execute(
                    """INSERT INTO finding_embeddings
                    (id, incident_id, investigation_id, service, category, statement, suggested_next_step, embedding)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (id) DO UPDATE SET
                        investigation_id = EXCLUDED.investigation_id,
                        service = EXCLUDED.service,
                        statement = EXCLUDED.statement,
                        suggested_next_step = EXCLUDED.suggested_next_step,
                        embedding = EXCLUDED.embedding""",
                    (
                        _record_id(result["incident_id"], finding["category"]),
                        UUID(result["incident_id"]),
                        UUID(result.get("investigation_id") or str(uuid5(NAMESPACE_URL, result["incident_id"]))),
                        service,
                        finding["category"],
                        finding["statement"],
                        finding.get("suggested_next_step"),
                        Jsonb(embedding),
                    ),
                )

    def count(self) -> int:
        with psycopg.connect(self.database_url) as connection:
            row = connection.execute("SELECT COUNT(DISTINCT incident_id) FROM finding_embeddings").fetchone()
        return int(row[0])

    def search(
        self,
        query_embedding: list[float],
        limit: int,
        exclude_incident_id: str | None = None,
    ) -> list[dict[str, Any]]:
        query = """SELECT id, incident_id, service, category, statement, suggested_next_step, embedding
                   FROM finding_embeddings"""
        parameters: tuple[Any, ...] = ()
        if exclude_incident_id is not None:
            query += " WHERE incident_id <> %s"
            parameters = (UUID(exclude_incident_id),)
        query += " ORDER BY created_at DESC LIMIT 500"
        with psycopg.connect(self.database_url, row_factory=dict_row) as connection:
            rows = connection.execute(query, parameters).fetchall()
        ranked = sorted(
            rows,
            key=lambda row: cosine_similarity(query_embedding, row["embedding"]),
            reverse=True,
        )
        return [
            {
                "id": str(row["id"]),
                "incident_id": str(row["incident_id"]),
                "service": row["service"],
                "category": row["category"],
                "statement": row["statement"],
                "suggested_next_step": row["suggested_next_step"],
                "similarity": round(cosine_similarity(query_embedding, row["embedding"]), 4),
            }
            for row in ranked[: max(0, limit)]
        ]


def _record_id(incident_id: str, category: str) -> UUID:
    return uuid5(NAMESPACE_URL, f"{incident_id}:{category}")

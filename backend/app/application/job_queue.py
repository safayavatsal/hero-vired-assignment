import os
from datetime import datetime, timedelta, timezone
from typing import Any
from uuid import UUID, uuid4

import psycopg
from psycopg.rows import dict_row
from psycopg.types.json import Jsonb


DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/hero_vired")


class JobRepository:
    def __init__(self, database_url: str = DATABASE_URL, lease_seconds: int = 60, max_attempts: int = 3) -> None:
        self.database_url = database_url
        self.lease_seconds = lease_seconds
        self.max_attempts = max_attempts

    def enqueue(self, job_type: str, incident_id: UUID | None, payload: dict[str, Any], idempotency_key: str) -> dict[str, Any]:
        now = datetime.now(timezone.utc)
        with psycopg.connect(self.database_url, row_factory=dict_row) as connection:
            row = connection.execute(
                """INSERT INTO jobs
                (id, incident_id, job_type, status, payload, idempotency_key, attempts, max_attempts, created_at, updated_at)
                VALUES (%s, %s, %s, 'queued', %s, %s, 0, %s, %s, %s)
                ON CONFLICT (idempotency_key) DO UPDATE SET updated_at = jobs.updated_at
                RETURNING *""",
                (uuid4(), incident_id, job_type, Jsonb(payload), idempotency_key, self.max_attempts, now, now),
            ).fetchone()
            return self._serialize(row)

    def claim(self, job_type: str | None = None) -> dict[str, Any] | None:
        now = datetime.now(timezone.utc)
        lease_until = now + timedelta(seconds=self.lease_seconds)
        with psycopg.connect(self.database_url, row_factory=dict_row) as connection:
            with connection.transaction():
                query = """SELECT * FROM jobs
                    WHERE (status = 'queued' OR (status = 'leased' AND lease_until <= %s))"""
                params: list[Any] = [now]
                if job_type:
                    query += " AND job_type = %s"
                    params.append(job_type)
                query += " ORDER BY created_at FOR UPDATE SKIP LOCKED LIMIT 1"
                row = connection.execute(query, params).fetchone()
                if row is None:
                    return None
                updated = connection.execute(
                    """UPDATE jobs SET status = 'leased', attempts = attempts + 1,
                    lease_until = %s, updated_at = %s WHERE id = %s RETURNING *""",
                    (lease_until, now, row["id"]),
                ).fetchone()
                return self._serialize(updated)

    def latest_for_incident(self, incident_id: UUID, job_type: str) -> dict[str, Any] | None:
        with psycopg.connect(self.database_url, row_factory=dict_row) as connection:
            row = connection.execute(
                """SELECT * FROM jobs
                   WHERE incident_id = %s AND job_type = %s
                   ORDER BY created_at DESC LIMIT 1""",
                (incident_id, job_type),
            ).fetchone()
            return self._serialize(row) if row is not None else None

    def complete(self, job_id: UUID) -> None:
        with psycopg.connect(self.database_url) as connection:
            connection.execute(
                "UPDATE jobs SET status = 'succeeded', lease_until = NULL, updated_at = %s WHERE id = %s",
                (datetime.now(timezone.utc), job_id),
            )

    def fail(self, job_id: UUID, error: str) -> None:
        with psycopg.connect(self.database_url, row_factory=dict_row) as connection:
            row = connection.execute("SELECT attempts, max_attempts FROM jobs WHERE id = %s", (job_id,)).fetchone()
            if row is None:
                return
            status = "dead_lettered" if row["attempts"] >= row["max_attempts"] else "queued"
            connection.execute(
                "UPDATE jobs SET status = %s, last_error = %s, lease_until = NULL, updated_at = %s WHERE id = %s",
                (status, error, datetime.now(timezone.utc), job_id),
            )

    @staticmethod
    def _serialize(row: dict[str, Any]) -> dict[str, Any]:
        return {
            key: value.isoformat() if isinstance(value, datetime) else str(value) if isinstance(value, UUID) else value
            for key, value in row.items()
        }

import os
from datetime import datetime, timedelta, timezone
from typing import Any
from uuid import UUID, uuid4

import psycopg
from psycopg.rows import dict_row
from psycopg.types.json import Jsonb

from app.application.resilience import env_float


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
                    WHERE ((status = 'queued' AND available_at <= %s) OR (status = 'leased' AND lease_until <= %s))"""
                params: list[Any] = [now, now]
                if job_type:
                    query += " AND job_type = %s"
                    params.append(job_type)
                query += " ORDER BY created_at FOR UPDATE SKIP LOCKED LIMIT 1"
                row = connection.execute(query, params).fetchone()
                if row is None:
                    return None
                updated = connection.execute(
                    """UPDATE jobs SET status = 'leased', attempts = attempts + 1,
                    lease_until = %s, leased_at = %s, updated_at = %s WHERE id = %s RETURNING *""",
                    (lease_until, now, now, row["id"]),
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
        now = datetime.now(timezone.utc)
        with psycopg.connect(self.database_url) as connection:
            connection.execute(
                "UPDATE jobs SET status = 'succeeded', lease_until = NULL, completed_at = %s, updated_at = %s WHERE id = %s",
                (now, now, job_id),
            )

    def fail(self, job_id: UUID, error: str) -> None:
        with psycopg.connect(self.database_url, row_factory=dict_row) as connection:
            row = connection.execute("SELECT attempts, max_attempts FROM jobs WHERE id = %s", (job_id,)).fetchone()
            if row is None:
                return
            status = "dead_lettered" if row["attempts"] >= row["max_attempts"] else "queued"
            available_at = datetime.now(timezone.utc) + timedelta(
                seconds=env_float("JOB_RETRY_BACKOFF_SECONDS", 2.0, 0.1, 60.0) * (2 ** max(row["attempts"] - 1, 0))
            )
            connection.execute(
                "UPDATE jobs SET status = %s, last_error = %s, available_at = %s, lease_until = NULL, updated_at = %s WHERE id = %s",
                (status, error, available_at, datetime.now(timezone.utc), job_id),
            )

    def metrics(self, job_type: str | None = None) -> dict[str, Any]:
        filters = " WHERE job_type = %s" if job_type else ""
        parameters = (job_type,) if job_type else ()
        query = f"""
            SELECT
                COUNT(*) FILTER (WHERE status = 'queued') AS queued,
                COUNT(*) FILTER (WHERE status = 'leased') AS leased,
                COUNT(*) FILTER (WHERE status = 'succeeded') AS succeeded,
                COUNT(*) FILTER (WHERE status = 'dead_lettered') AS dead_lettered,
                COUNT(*) FILTER (WHERE last_error IS NOT NULL AND status IN ('queued', 'leased')) AS retrying,
                COALESCE(EXTRACT(EPOCH FROM (CURRENT_TIMESTAMP - MIN(created_at)
                    FILTER (WHERE status IN ('queued', 'leased')))) * 1000, 0) AS oldest_pending_age_ms,
                COALESCE(AVG(EXTRACT(EPOCH FROM (leased_at - created_at)) * 1000)
                    FILTER (WHERE leased_at IS NOT NULL), 0) AS average_wait_ms,
                COALESCE(AVG(EXTRACT(EPOCH FROM (completed_at - leased_at)) * 1000)
                    FILTER (WHERE leased_at IS NOT NULL AND completed_at IS NOT NULL), 0) AS average_processing_ms
            FROM jobs{filters}
        """
        with psycopg.connect(self.database_url, row_factory=dict_row) as connection:
            row = connection.execute(query, parameters).fetchone()
        return {
            "queue": "postgresql",
            "job_type": job_type,
            "queued": int(row["queued"] or 0),
            "leased": int(row["leased"] or 0),
            "succeeded": int(row["succeeded"] or 0),
            "dead_lettered": int(row["dead_lettered"] or 0),
            "retrying": int(row["retrying"] or 0),
            "oldest_pending_age_ms": max(0, int(float(row["oldest_pending_age_ms"] or 0))),
            "average_wait_ms": max(0, round(float(row["average_wait_ms"] or 0), 2)),
            "average_processing_ms": max(0, round(float(row["average_processing_ms"] or 0), 2)),
        }

    @staticmethod
    def _serialize(row: dict[str, Any]) -> dict[str, Any]:
        return {
            key: value.isoformat() if isinstance(value, datetime) else str(value) if isinstance(value, UUID) else value
            for key, value in row.items()
        }

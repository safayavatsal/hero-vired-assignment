import os
from uuid import UUID, uuid4

import psycopg
import pytest
from fastapi.testclient import TestClient

from app.application.job_queue import JobRepository
from app.main import app
from app.migrations import run_migrations


DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://postgres:postgres@localhost:5432/hero_vired",
)


def _database_available() -> bool:
    try:
        with psycopg.connect(DATABASE_URL, connect_timeout=1):
            return True
    except psycopg.Error:
        return False


pytestmark = pytest.mark.skipif(
    not _database_available(),
    reason="queue integration tests require the configured PostgreSQL service",
)


def _cleanup(prefix: str) -> None:
    with psycopg.connect(DATABASE_URL) as connection:
        connection.execute("DELETE FROM jobs WHERE idempotency_key LIKE %s", (f"{prefix}%",))


def test_job_metrics_report_pending_retry_and_processing_state() -> None:
    run_migrations(DATABASE_URL)
    prefix = f"queue-metrics-{uuid4()}"
    repository = JobRepository(DATABASE_URL, lease_seconds=60, max_attempts=3)
    try:
        retrying = repository.enqueue("queue-test", None, {}, f"{prefix}-retrying")
        retrying_claim = repository.claim("queue-test")
        assert retrying_claim is not None
        assert retrying_claim["id"] == retrying["id"]
        repository.fail(UUID(retrying_claim["id"]), "temporary failure")

        completed = repository.enqueue("queue-test", None, {}, f"{prefix}-completed")
        completed_claim = repository.claim("queue-test")
        assert completed_claim is not None
        assert completed_claim["id"] == completed["id"]
        repository.complete(UUID(completed_claim["id"]))
        pending = repository.enqueue("queue-test", None, {}, f"{prefix}-pending")

        metrics = repository.metrics("queue-test")

        assert pending["status"] == "queued"
        assert metrics["queued"] >= 2
        assert metrics["succeeded"] >= 1
        assert metrics["retrying"] >= 1
        assert metrics["dead_lettered"] >= 0
        assert metrics["oldest_pending_age_ms"] >= 0
        assert metrics["average_wait_ms"] >= 0
        assert metrics["average_processing_ms"] >= 0
    finally:
        _cleanup(prefix)


def test_expired_lease_is_reclaimed_without_duplicate_job() -> None:
    run_migrations(DATABASE_URL)
    prefix = f"queue-lease-{uuid4()}"
    repository = JobRepository(DATABASE_URL, lease_seconds=60, max_attempts=3)
    try:
        queued = repository.enqueue("queue-test", None, {}, f"{prefix}-job")
        claimed = repository.claim("queue-test")
        assert claimed is not None
        assert claimed["id"] == queued["id"]

        with psycopg.connect(DATABASE_URL) as connection:
            connection.execute(
                "UPDATE jobs SET lease_until = NOW() - INTERVAL '1 second' WHERE id = %s",
                (claimed["id"],),
            )

        reclaimed = repository.claim("queue-test")

        assert reclaimed is not None
        assert reclaimed["id"] == claimed["id"]
        assert reclaimed["attempts"] == 2
    finally:
        _cleanup(prefix)


def test_duplicate_enqueue_returns_the_original_job() -> None:
    run_migrations(DATABASE_URL)
    prefix = f"queue-idempotency-{uuid4()}"
    repository = JobRepository(DATABASE_URL)
    try:
        first = repository.enqueue("queue-test", None, {"value": 1}, f"{prefix}-job")
        second = repository.enqueue("queue-test", None, {"value": 2}, f"{prefix}-job")

        assert second["id"] == first["id"]
        assert second["payload"] == {"value": 1}
    finally:
        _cleanup(prefix)


def test_queue_metrics_endpoint_returns_bounded_values() -> None:
    response = TestClient(app).get("/api/v1/jobs/metrics")

    assert response.status_code == 200
    payload = response.json()
    assert payload["queue"] == "postgresql"
    assert payload["queued"] >= 0
    assert payload["oldest_pending_age_ms"] >= 0

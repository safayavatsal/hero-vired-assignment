#!/usr/bin/env python3
import argparse
import os
import sys
from time import monotonic
from typing import Any
from uuid import UUID, uuid4


def run_benchmark(queue: Any, count: int) -> dict[str, Any]:
    started = monotonic()
    completed = 0
    failed = 0
    for _ in range(count):
        job = queue.enqueue("queue-benchmark", None, {}, f"queue-benchmark-{uuid4()}")
        claimed = queue.claim("queue-benchmark")
        if claimed is None or claimed["id"] != job["id"]:
            failed += 1
            continue
        queue.complete(UUID(claimed["id"]))
        completed += 1
    elapsed_ms = (monotonic() - started) * 1000
    result = {
        "queue": "postgresql",
        "requested": count,
        "completed": completed,
        "failed": failed,
        "elapsed_ms": round(elapsed_ms, 2),
        "jobs_per_second": round(completed / max(elapsed_ms / 1000, 0.001), 2),
    }
    metrics = getattr(queue, "metrics", None)
    if metrics is not None:
        result["metrics"] = metrics("queue-benchmark")
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description="Measure the local durable queue path.")
    parser.add_argument("--count", type=int, default=20)
    args = parser.parse_args()
    if args.count < 1 or args.count > 500:
        parser.error("--count must be between 1 and 500")

    backend_path = os.path.join(os.path.dirname(__file__), "..", "backend")
    sys.path.insert(0, os.path.abspath(backend_path))
    from app.application.job_queue import JobRepository
    from app.migrations import run_migrations

    database_url = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/hero_vired")
    run_migrations(database_url)
    print(result_json(run_benchmark(JobRepository(database_url), args.count)))
    return 0


def result_json(result: dict[str, Any]) -> str:
    import json

    return json.dumps(result, sort_keys=True)


if __name__ == "__main__":
    raise SystemExit(main())

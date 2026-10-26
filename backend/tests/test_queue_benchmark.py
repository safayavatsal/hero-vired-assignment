import importlib.util
from pathlib import Path
from uuid import UUID, uuid4


SCRIPT = Path(__file__).parents[2] / "scripts" / "benchmark-queue.py"
SPEC = importlib.util.spec_from_file_location("benchmark_queue", SCRIPT)
benchmark_queue = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(benchmark_queue)


class FakeQueue:
    def __init__(self):
        self.jobs = []

    def enqueue(self, job_type, incident_id, payload, idempotency_key):
        job = {"id": str(uuid4()), "job_type": job_type, "status": "queued"}
        self.jobs.append(job)
        return job

    def claim(self, job_type=None):
        for job in self.jobs:
            if job["status"] == "queued" and (job_type is None or job["job_type"] == job_type):
                job["status"] = "leased"
                return job
        return None

    def complete(self, job_id: UUID):
        for job in self.jobs:
            if job["id"] == str(job_id):
                job["status"] = "succeeded"

    def metrics(self, job_type=None):
        return {"job_type": job_type, "succeeded": sum(job["status"] == "succeeded" for job in self.jobs)}


def test_queue_benchmark_reports_completed_work():
    result = benchmark_queue.run_benchmark(FakeQueue(), 3)

    assert result["requested"] == 3
    assert result["completed"] == 3
    assert result["failed"] == 0
    assert result["jobs_per_second"] >= 0
    assert result["metrics"]["succeeded"] == 3

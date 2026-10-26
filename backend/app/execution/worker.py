import os
import time
from uuid import UUID

from app.application.job_queue import JobRepository
from app.application.workflow import WorkflowService
from app.application.incident import investigation_service
from app.ports.job_queue import JobQueue


class Worker:
    def __init__(self, poll_interval: float = 1.0, jobs: JobQueue | None = None) -> None:
        self.poll_interval = poll_interval
        self.jobs = jobs or JobRepository()
        self.workflow = WorkflowService()
        self.investigation = investigation_service

    def run_once(self) -> None:
        self.workflow.recover_overdue_pages()
        job = self.jobs.claim()
        if job is None:
            return
        try:
            if job["job_type"] == "action":
                self.workflow.execute_claimed_action(UUID(job["payload"]["action_id"]))
            elif job["job_type"] == "investigation":
                self.investigation.investigate(UUID(job["payload"]["incident_id"]), job["payload"]["scenario_id"])
            else:
                raise ValueError(f"unsupported job type: {job['job_type']}")
        except Exception as error:
            self.jobs.fail(UUID(job["id"]), str(error))
        else:
            self.jobs.complete(UUID(job["id"]))

    def run(self) -> None:
        while True:
            try:
                self.run_once()
            except Exception:
                time.sleep(self.poll_interval)
                continue
            time.sleep(self.poll_interval)


if __name__ == "__main__":
    Worker(float(os.getenv("WORKER_POLL_INTERVAL", "1"))).run()

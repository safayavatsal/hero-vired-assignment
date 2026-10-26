from uuid import uuid4

from app.execution import worker as worker_module


class FakeJobs:
    def __init__(self):
        self.job = {"id": str(uuid4()), "job_type": "action", "payload": {"action_id": str(uuid4())}}
        self.completed = []
        self.failed = []

    def claim(self):
        job, self.job = self.job, None
        return job

    def complete(self, job_id):
        self.completed.append(job_id)

    def fail(self, job_id, error):
        self.failed.append((job_id, error))


class FakeWorkflow:
    def __init__(self):
        self.recovered = 0
        self.executed = []

    def recover_overdue_pages(self):
        self.recovered += 1

    def execute_claimed_action(self, action_id):
        self.executed.append(action_id)


class FakeInvestigation:
    def __init__(self):
        self.executed = []

    def investigate(self, incident_id, scenario_id):
        self.executed.append((incident_id, scenario_id))


def test_worker_claims_executes_and_completes_action(monkeypatch):
    jobs = FakeJobs()
    workflow = FakeWorkflow()
    monkeypatch.setattr(worker_module, "JobRepository", lambda: jobs)
    monkeypatch.setattr(worker_module, "WorkflowService", lambda: workflow)

    worker = worker_module.Worker()
    worker.run_once()

    assert workflow.recovered == 1
    assert len(workflow.executed) == 1
    assert len(jobs.completed) == 1
    assert jobs.failed == []


def test_worker_claims_executes_investigation(monkeypatch):
    jobs = FakeJobs()
    incident_id = uuid4()
    jobs.job = {"id": str(uuid4()), "job_type": "investigation", "payload": {
        "incident_id": str(incident_id), "scenario_id": "disk_pressure",
    }}
    workflow = FakeWorkflow()
    investigation = FakeInvestigation()
    monkeypatch.setattr(worker_module, "JobRepository", lambda: jobs)
    monkeypatch.setattr(worker_module, "WorkflowService", lambda: workflow)
    monkeypatch.setattr(worker_module, "investigation_service", investigation)

    worker = worker_module.Worker()
    worker.run_once()

    assert investigation.executed == [(incident_id, "disk_pressure")]
    assert len(jobs.completed) == 1
    assert jobs.failed == []


def test_worker_accepts_an_injected_queue():
    jobs = FakeJobs()
    workflow = FakeWorkflow()

    worker = worker_module.Worker(jobs=jobs)
    worker.workflow = workflow
    worker.run_once()

    assert workflow.recovered == 1
    assert len(jobs.completed) == 1

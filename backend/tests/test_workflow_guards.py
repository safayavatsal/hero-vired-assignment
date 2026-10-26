from uuid import uuid4

import pytest

from app.application import workflow as workflow_module
from app.api.workflow import PageRequest
from app.application.workflow import WorkflowService


class _Connection:
    def __init__(self, version: int) -> None:
        self.version = version

    def execute(self, _query, _params):
        return _Result({"version": self.version})


class _Result:
    def __init__(self, row):
        self.row = row

    def fetchone(self):
        return self.row


class _Context:
    def __init__(self, value):
        self.value = value

    def __enter__(self):
        return self.value

    def __exit__(self, *_args):
        return False


def test_human_decision_version_guard_rejects_stale_state() -> None:
    with pytest.raises(ValueError, match="incident version conflict"):
        WorkflowService._check_version(_Connection(3), uuid4(), 2)


def test_human_decision_version_guard_allows_current_state() -> None:
    WorkflowService._check_version(_Connection(3), uuid4(), 3)


def test_page_context_uses_latest_finding(monkeypatch) -> None:
    class Investigation:
        def get(self, _incident_id):
            return {"findings": [{"statement": "latency is high", "suggested_next_step": "rollback"}]}

    monkeypatch.setattr("app.application.incident.investigation_service", Investigation())

    context = WorkflowService._investigation_page_context(uuid4())
    assert context["evidence_summary"] == "latency is high"
    assert context["suggested_next_step"] == "rollback"


def test_verification_uses_persisted_worker_result_when_simulator_state_is_local(monkeypatch) -> None:
    def missing_action(_action_id):
        raise ValueError("action not found")

    monkeypatch.setattr(workflow_module.simulator_service, "verify_action", missing_action)
    result = WorkflowService._verify_simulator_result({
        "simulator_action_id": str(uuid4()),
        "result": {"status": "completed", "state_after": {"healthy": True}},
    })

    assert result["status"] == "completed"
    assert result["verified"] is True
    assert "verified_at" in result


def test_page_response_allows_reply_after_acknowledgement(monkeypatch) -> None:
    page_id = uuid4()
    incident_id = uuid4()

    class _Connection:
        def execute(self, query, _params):
            if "SELECT * FROM pages" in query:
                return _Result({"id": page_id, "incident_id": incident_id, "status": "acknowledged"})
            return _Result(None)

    monkeypatch.setattr(workflow_module.psycopg, "connect", lambda *args, **kwargs: _Context(_Connection()))
    monkeypatch.setattr(WorkflowService, "_check_version", staticmethod(lambda *_args: None))
    monkeypatch.setattr(WorkflowService, "_timeline", staticmethod(lambda *_args: None))
    monkeypatch.setattr(WorkflowService, "_get_page", staticmethod(lambda _connection, page_id: {"id": str(page_id), "status": "replied"}))

    result = WorkflowService("postgresql://test").respond(page_id, "reply", "Investigating")

    assert result == {"id": str(page_id), "status": "replied"}


def test_page_response_allows_acknowledgement_after_owner_note(monkeypatch) -> None:
    page_id = uuid4()
    incident_id = uuid4()

    class _Connection:
        def execute(self, query, _params):
            if "SELECT * FROM pages" in query:
                return _Result({"id": page_id, "incident_id": incident_id, "status": "replied"})
            return _Result(None)

    monkeypatch.setattr(workflow_module.psycopg, "connect", lambda *args, **kwargs: _Context(_Connection()))
    monkeypatch.setattr(WorkflowService, "_check_version", staticmethod(lambda *_args: None))
    monkeypatch.setattr(WorkflowService, "_timeline", staticmethod(lambda *_args: None))
    monkeypatch.setattr(WorkflowService, "_get_page", staticmethod(lambda _connection, page_id: {"id": str(page_id), "status": "acknowledged"}))

    result = WorkflowService("postgresql://test").respond(page_id, "acknowledge", "Taking ownership")

    assert result == {"id": str(page_id), "status": "acknowledged"}


def test_page_request_supports_recipient_email_and_self_ownership() -> None:
    request = PageRequest(responder_email="owner@example.test", notify=False)

    assert request.responder_email == "owner@example.test"
    assert request.notify is False


def test_self_ownership_creates_acknowledged_page_without_delivery(monkeypatch) -> None:
    incident_id = uuid4()
    page_id = uuid4()

    class Connection:
        def execute(self, _query, _params):
            return _Result(None)

    service = WorkflowService("postgresql://test")
    monkeypatch.setattr(service, "_incident", lambda _incident_id: {
        "id": str(incident_id), "service": "orders-worker", "severity": "high",
        "summary": "disk pressure", "version": 1,
    })
    monkeypatch.setattr(service.ownership_gateway, "resolve", lambda *_args: None)
    monkeypatch.setattr(service.notification_gateway, "deliver", lambda _payload: pytest.fail("self ownership sent a notification"))
    monkeypatch.setattr(workflow_module.psycopg, "connect", lambda *args, **kwargs: _Context(Connection()))
    monkeypatch.setattr(WorkflowService, "_timeline", staticmethod(lambda *_args: None))
    monkeypatch.setattr(WorkflowService, "_get_page", staticmethod(lambda _connection, _page_id: {
        "id": str(page_id), "status": "acknowledged", "response_type": "acknowledge",
    }))

    result = service.create_page(incident_id, "local-operator", None, 300, notify=False)

    assert result["page"]["status"] == "acknowledged"

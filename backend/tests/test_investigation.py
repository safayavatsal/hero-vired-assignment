import time
import pytest
from uuid import uuid4

from app.application.investigation import InvestigationService
from app.application.simulator import SimulatorService
from app.application.model_gateway import (
    DEFAULT_MODEL_GATEWAY_URL,
    HttpModelGateway,
    _openai_request,
    _openai_response,
    mask_sensitive,
    validate_model_response,
)


class ExistingIncident:
    def __init__(self, service=None, status="received"):
        self.incident = {"id": str(uuid4()), "status": status, "version": 1}
        if service is not None:
            self.incident["service"] = service

    def get_incident(self, incident_id):
        self.incident["id"] = str(incident_id)
        return self.incident

    def transition(self, incident_id, target_status, expected_version):
        assert target_status in {"investigating", "unfixable"}
        self.incident["status"] = target_status
        self.incident["version"] += 1
        return dict(self.incident)

    def append_timeline_event(self, incident_id, event_type, payload):
        self.incident.setdefault("timeline", []).append({"event_type": event_type, "payload": payload})


class MemoryInvestigationRepository:
    def __init__(self) -> None:
        self.results = {}

    def initialize(self) -> None:
        return None

    def save(self, result) -> None:
        self.results[result["incident_id"]] = result

    def get(self, incident_id):
        return self.results.get(str(incident_id))


class PartialEvidenceProvider(SimulatorService):
    def query_evidence(self, source_type):
        if source_type == "logs":
            raise TimeoutError("logs provider timed out")
        return super().query_evidence(source_type)


class ContradictoryEvidenceProvider(SimulatorService):
    def query_evidence(self, source_type):
        response = super().query_evidence(source_type)
        if source_type == "metrics":
            response["items"] = response["items"] + [dict(response["items"][0])]
            response["items"][-1]["value"] = response["items"][0]["value"] + 1
        return response


class InvalidModelGateway:
    def analyze(self, prompt):
        return {"evidence_ids": ["not-collected"]}


class CompletedModelGateway:
    def analyze(self, prompt):
        evidence_ids = [item["id"] for item in prompt["evidence"]]
        return {
            "current_condition": "latency is elevated",
            "likely_cause": "a recent deployment",
            "confidence": 0.9,
            "suggested_next_step": "rollback",
            "evidence_ids": evidence_ids,
            "uncertainty": None,
        }


def test_investigation_findings_cite_collected_evidence(monkeypatch) -> None:
    monkeypatch.delenv("MODEL_GATEWAY_TOKEN", raising=False)
    service = InvestigationService(ExistingIncident(), SimulatorService(), MemoryInvestigationRepository())

    result = service.investigate(uuid4(), "deployment_regression")

    finding = result["findings"][0]
    evidence_ids = {item["id"] for item in result["evidence"]}
    assert finding["category"] == "deployment_regression"
    assert set(finding["evidence_ids"]).issubset(evidence_ids)
    assert [item["tool"] for item in result["tool_trace"]] == [
        "simulator.evidence.logs", "simulator.evidence.metrics",
        "simulator.evidence.deploys", "simulator.evidence.service_health",
    ]
    assert result["model_telemetry"]["status"] == "unavailable"


def test_third_party_outage_has_no_local_action() -> None:
    service = InvestigationService(ExistingIncident(), SimulatorService(), MemoryInvestigationRepository())

    result = service.investigate(uuid4(), "third_party_outage")

    assert result["findings"][0]["suggested_next_step"] == "unfixable"


def test_investigation_can_be_read_after_service_memory_is_cleared() -> None:
    repository = MemoryInvestigationRepository()
    incident_id = uuid4()
    service = InvestigationService(ExistingIncident(), SimulatorService(), repository)
    service.investigate(incident_id, "disk_pressure")

    restarted_service = InvestigationService(ExistingIncident(), SimulatorService(), repository)

    assert restarted_service.get(incident_id)["scenario_id"] == "disk_pressure"


def test_unavailable_evidence_is_visible_in_findings() -> None:
    service = InvestigationService(ExistingIncident(), PartialEvidenceProvider(), MemoryInvestigationRepository())

    result = service.investigate(uuid4(), "deployment_regression")

    assert result["evidence"][0]["availability"] == "unavailable"
    assert "logs" in result["findings"][0]["uncertainty"]


def test_slow_evidence_source_is_bounded(monkeypatch) -> None:
    class SlowEvidenceProvider(SimulatorService):
        def query_evidence(self, source_type):
            if source_type == "logs":
                time.sleep(0.3)
            return super().query_evidence(source_type)

    monkeypatch.setenv("EVIDENCE_TIMEOUT_SECONDS", "0.1")
    service = InvestigationService(ExistingIncident(), SlowEvidenceProvider(), MemoryInvestigationRepository())

    result = service.investigate(uuid4(), "disk_pressure")

    assert result["evidence"][0]["availability"] == "unavailable"
    assert "timed out" in result["evidence"][0]["items"][0]["error"]
    assert result["evidence"][0]["query"] == "simulator.evidence.logs"
    assert result["evidence"][0]["parameters"] == {"source_type": "logs"}
    assert result["evidence"][0]["error"] == "evidence provider timed out"


def test_model_gateway_is_safe_when_unconfigured(monkeypatch) -> None:
    monkeypatch.delenv("MODEL_GATEWAY_TOKEN", raising=False)
    service = InvestigationService(ExistingIncident(), SimulatorService(), MemoryInvestigationRepository())

    result = service.investigate(uuid4(), "disk_pressure")

    assert result["model_status"] == "unavailable"


def test_model_gateway_uses_configured_url_and_format(monkeypatch) -> None:
    monkeypatch.setenv("MODEL_GATEWAY_TOKEN", "test-token")
    monkeypatch.setenv("MODEL_GATEWAY_URL", "https://provider.test/responses")
    monkeypatch.setenv("MODEL_GATEWAY_FORMAT", "openai_responses")

    service = InvestigationService(ExistingIncident(), SimulatorService(), MemoryInvestigationRepository())

    assert isinstance(service.model_gateway, HttpModelGateway)
    assert service.model_gateway.url == "https://provider.test/responses"
    assert service.model_gateway.response_format == "openai_responses"


def test_model_gateway_uses_default_url_when_url_is_unset(monkeypatch) -> None:
    monkeypatch.setenv("MODEL_GATEWAY_TOKEN", "test-token")
    monkeypatch.delenv("MODEL_GATEWAY_URL", raising=False)
    monkeypatch.delenv("MODEL_GATEWAY_FORMAT", raising=False)

    service = InvestigationService(ExistingIncident(), SimulatorService(), MemoryInvestigationRepository())

    assert isinstance(service.model_gateway, HttpModelGateway)
    assert service.model_gateway.url == DEFAULT_MODEL_GATEWAY_URL
    assert service.model_gateway.response_format == "openai_responses"


def test_invalid_model_citations_are_rejected() -> None:
    service = InvestigationService(
        ExistingIncident(), SimulatorService(), MemoryInvestigationRepository(), InvalidModelGateway()
    )

    result = service.investigate(uuid4(), "disk_pressure")

    assert result["model_status"] == "failed"


def test_model_response_validation_rejects_malformed_structured_output() -> None:
    with pytest.raises(ValueError, match="non-empty string"):
        validate_model_response({
            "current_condition": "",
            "likely_cause": "release",
            "confidence": 0.9,
            "suggested_next_step": "rollback",
            "evidence_ids": [],
            "uncertainty": None,
        }, set())


def test_sensitive_values_are_masked_before_model_use() -> None:
    masked = mask_sensitive({"token": "secret-value", "message": "Bearer abc123"})

    assert masked == {"token": "[REDACTED]", "message": "Bearer [REDACTED]"}


def test_evidence_returned_to_reviewers_is_masked() -> None:
    class SecretEvidenceProvider(SimulatorService):
        def query_evidence(self, source_type):
            response = super().query_evidence(source_type)
            response["items"] = [{"message": "Bearer secret-value"}]
            return response

    service = InvestigationService(ExistingIncident(), SecretEvidenceProvider(), MemoryInvestigationRepository())

    result = service.investigate(uuid4(), "disk_pressure")

    assert result["evidence"][0]["items"] == [{"message": "Bearer [REDACTED]"}]


def test_contradictory_metrics_are_visible_in_uncertainty() -> None:
    service = InvestigationService(ExistingIncident(), ContradictoryEvidenceProvider(), MemoryInvestigationRepository())

    result = service.investigate(uuid4(), "deployment_regression")

    assert "Conflicting metric values" in result["findings"][0]["uncertainty"]


def test_openai_responses_adapter_uses_structured_output() -> None:
    request = _openai_request({"instruction": "inspect"}, "test-model")
    assert request["model"] == "test-model"
    assert request["text"]["format"]["type"] == "json_schema"

    response = _openai_response({"output_text": '{"current_condition":"bad","likely_cause":"release","confidence":0.9,"suggested_next_step":"rollback","evidence_ids":[],"uncertainty":null}'})
    assert response["suggested_next_step"] == "rollback"


def test_model_analysis_and_telemetry_are_returned_for_a_realistic_incident() -> None:
    service = InvestigationService(
        ExistingIncident("payments-api"), SimulatorService(), MemoryInvestigationRepository(), CompletedModelGateway()
    )

    result = service.investigate(uuid4(), "deployment_regression")

    assert result["model_status"] == "completed"
    assert result["model_analysis"]["evidence_ids"]
    assert result["model_telemetry"]["status"] == "completed"
    logs = next(item for item in result["evidence"] if item["source_type"] == "logs")
    assert logs["items"][0]["route"] == "POST /v1/payments/authorize"


def test_same_evidence_uses_versioned_cache() -> None:
    service = InvestigationService(ExistingIncident(), SimulatorService(), MemoryInvestigationRepository())
    incident_id = uuid4()

    first = service.investigate(incident_id, "disk_pressure")
    second = service.investigate(incident_id, "disk_pressure")

    assert first is second
    assert first["prompt_version"] == "investigation-v1"


def test_persisted_investigation_is_idempotent_after_service_restart(monkeypatch) -> None:
    monkeypatch.delenv("MODEL_GATEWAY_TOKEN", raising=False)
    repository = MemoryInvestigationRepository()
    incident_id = uuid4()
    first = InvestigationService(ExistingIncident(), SimulatorService(), repository)
    original = first.investigate(incident_id, "disk_pressure")

    restarted = InvestigationService(ExistingIncident(), SimulatorService(), repository)
    assert restarted.investigate(incident_id, "disk_pressure") == original


def test_queued_persisted_investigation_reapplies_incident_state() -> None:
    class Jobs:
        def enqueue(self, *_args):
            return {"status": "queued"}

    incident_service = ExistingIncident()
    repository = MemoryInvestigationRepository()
    incident_id = uuid4()
    InvestigationService(incident_service, SimulatorService(), repository).investigate(incident_id, "disk_pressure")
    incident_service.incident["status"] = "received"

    result = InvestigationService(incident_service, SimulatorService(), repository, jobs=Jobs()).enqueue(incident_id, "disk_pressure")

    assert result["status"] == "completed"
    assert incident_service.incident["status"] == "investigating"


def test_deeper_investigation_bypasses_completed_result() -> None:
    class Jobs:
        def __init__(self):
            self.calls = []

        def enqueue(self, *args):
            self.calls.append(args)
            return {"id": str(uuid4()), "status": "queued", "payload": args[2]}

    incident_id = uuid4()
    incident_service = ExistingIncident(service="orders-worker", status="investigating")
    repository = MemoryInvestigationRepository()
    service = InvestigationService(incident_service, SimulatorService(), repository)
    service.investigate(incident_id, "disk_pressure")
    jobs = Jobs()

    result = InvestigationService(incident_service, SimulatorService(), repository, jobs=jobs).enqueue(
        incident_id, "disk_pressure", "deeper"
    )

    assert result["status"] == "queued"
    assert jobs.calls[0][2]["mode"] == "deeper"
    assert jobs.calls[0][3].endswith(":deeper")


def test_persisted_unavailable_investigation_retries_after_provider_configuration(monkeypatch) -> None:
    monkeypatch.delenv("MODEL_GATEWAY_TOKEN", raising=False)
    repository = MemoryInvestigationRepository()
    incident_id = uuid4()
    first = InvestigationService(ExistingIncident(), SimulatorService(), repository)
    unavailable = first.investigate(incident_id, "disk_pressure")
    assert unavailable["model_status"] == "unavailable"

    restarted = InvestigationService(
        ExistingIncident(), SimulatorService(), repository, CompletedModelGateway()
    )

    completed = restarted.investigate(incident_id, "disk_pressure")

    assert completed["model_status"] == "completed"
    assert completed["model_analysis"]["suggested_next_step"] == "rollback"


def test_investigation_transitions_received_incident_to_investigating() -> None:
    incident_service = ExistingIncident(service="orders-worker")
    service = InvestigationService(incident_service, SimulatorService(), MemoryInvestigationRepository())

    service.investigate(uuid4(), "disk_pressure")

    assert incident_service.incident["status"] == "investigating"
    assert incident_service.incident["timeline"][0]["event_type"] == "investigation_started"


def test_third_party_investigation_classifies_incident_as_unfixable() -> None:
    incident_service = ExistingIncident(service="checkout-api")
    service = InvestigationService(incident_service, SimulatorService(), MemoryInvestigationRepository())

    service.investigate(uuid4(), "third_party_outage")

    assert incident_service.incident["status"] == "unfixable"
    assert [event["event_type"] for event in incident_service.incident["timeline"]] == [
        "investigation_started", "investigation_completed", "incident_unfixable"
    ]


def test_investigation_rejects_cross_service_scenario() -> None:
    incident_service = ExistingIncident(service="feature57-api")
    service = InvestigationService(incident_service, SimulatorService(), MemoryInvestigationRepository())

    try:
        service.investigate(uuid4(), "deployment_regression")
    except ValueError as error:
        assert str(error) == "selected scenario does not match the incident service"
    else:
        raise AssertionError("cross-service investigation was accepted")


def test_registered_scenario_investigates_without_code_changes() -> None:
    simulator = SimulatorService()
    simulator.register_scenario("queue_backlog", {
        "name": "Queue backlog",
        "service": "notification-worker",
        "severity": "high",
        "alert_type": "queue_depth_high",
        "hidden_cause": "downstream consumer crashed and retries accumulated",
        "evidence": {
            "logs": [{"timestamp": "2026-10-25T09:00:00Z", "message": "consumer group lag rising", "level": "warn"}],
            "metrics": [{"name": "queue_depth", "value": 1200, "threshold": 200, "window": "5m"}],
            "deploys": [],
            "service_health": [{"service": "notification-worker", "healthy": True}],
        },
        "allowed_actions": ["restart", "scale"],
        "controls": {"evidence_slow": [], "action_timeout_after_completion": [], "responder_non_response": False, "third_party_outage": False},
        "initial_state": {"queue_depth": 1200, "healthy": True},
        "finding": {
            "metric": "queue_depth",
            "category": "queue_backlog",
            "statement": "The notification queue depth is far above its threshold after a consumer crash.",
            "confidence": 0.9,
            "suggested_next_step": "restart",
            "evidence_sources": ["metrics", "logs"],
            "uncertainty": None,
        },
    })

    incident_service = ExistingIncident(service="notification-worker")
    service = InvestigationService(incident_service, simulator, MemoryInvestigationRepository())

    result = service.investigate(uuid4(), "queue_backlog")

    finding = result["findings"][0]
    assert finding["category"] == "queue_backlog"
    assert finding["suggested_next_step"] == "restart"
    assert finding["confidence"] == 0.9
    evidence_ids = {item["id"] for item in result["evidence"]}
    assert set(finding["evidence_ids"]).issubset(evidence_ids)

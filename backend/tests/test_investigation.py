from uuid import uuid4

from app.application.investigation import InvestigationService
from app.application.simulator import SimulatorService
from app.application.model_gateway import mask_sensitive


class ExistingIncident:
    def get_incident(self, incident_id):
        return {"id": str(incident_id)}


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


def test_investigation_findings_cite_collected_evidence() -> None:
    service = InvestigationService(ExistingIncident(), SimulatorService(), MemoryInvestigationRepository())

    result = service.investigate(uuid4(), "deployment_regression")

    finding = result["findings"][0]
    evidence_ids = {item["id"] for item in result["evidence"]}
    assert finding["category"] == "deployment_regression"
    assert set(finding["evidence_ids"]).issubset(evidence_ids)


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


def test_model_gateway_is_safe_when_unconfigured() -> None:
    service = InvestigationService(ExistingIncident(), SimulatorService(), MemoryInvestigationRepository())

    result = service.investigate(uuid4(), "disk_pressure")

    assert result["model_status"] == "unavailable"


def test_invalid_model_citations_are_rejected() -> None:
    service = InvestigationService(
        ExistingIncident(), SimulatorService(), MemoryInvestigationRepository(), InvalidModelGateway()
    )

    result = service.investigate(uuid4(), "disk_pressure")

    assert result["model_status"] == "failed"


def test_sensitive_values_are_masked_before_model_use() -> None:
    masked = mask_sensitive({"token": "secret-value", "message": "Bearer abc123"})

    assert masked == {"token": "[REDACTED]", "message": "Bearer [REDACTED]"}


def test_contradictory_metrics_are_visible_in_uncertainty() -> None:
    service = InvestigationService(ExistingIncident(), ContradictoryEvidenceProvider(), MemoryInvestigationRepository())

    result = service.investigate(uuid4(), "deployment_regression")

    assert "Conflicting metric values" in result["findings"][0]["uncertainty"]


def test_same_evidence_uses_versioned_cache() -> None:
    service = InvestigationService(ExistingIncident(), SimulatorService(), MemoryInvestigationRepository())
    incident_id = uuid4()

    first = service.investigate(incident_id, "disk_pressure")
    second = service.investigate(incident_id, "disk_pressure")

    assert first is second
    assert first["prompt_version"] == "investigation-v1"

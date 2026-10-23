import json
from pathlib import Path
from uuid import UUID

from app.application.investigation import InvestigationService
from app.application.model_gateway import UnavailableModelGateway
from app.domain.simulator import SimulatorService


CASES = json.loads((Path(__file__).parents[1] / "evaluations" / "golden_cases.json").read_text())


class MemoryRepository:
    def __init__(self) -> None:
        self.results = {}

    def initialize(self) -> None:
        return None

    def save(self, result) -> None:
        self.results[result["incident_id"]] = result

    def get(self, incident_id):
        return self.results.get(str(incident_id))


class Incident:
    def __init__(self, service: str) -> None:
        self.value = {"id": "", "service": service, "status": "received", "version": 1}

    def get_incident(self, incident_id: UUID):
        self.value["id"] = str(incident_id)
        return self.value

    def transition(self, _incident_id, status, _version):
        self.value["status"] = status
        self.value["version"] += 1
        return self.value

    def append_timeline_event(self, _incident_id, _event_type, _payload):
        return None


def test_golden_investigations_cover_all_scenarios() -> None:
    for case in CASES:
        incident_id = UUID(int=CASES.index(case) + 1)
        service = InvestigationService(
            Incident(case["service"]),
            SimulatorService(),
            MemoryRepository(),
            model_gateway=UnavailableModelGateway(),
        )

        result = service.investigate(incident_id, case["scenario_id"])
        finding = result["findings"][0]
        evidence_ids = {item["id"] for item in result["evidence"]}
        source_types = {item["source_type"] for item in result["evidence"]}

        assert result["prompt_version"] == case["prompt_version"]
        assert result["prompt_contract_hash"] == case["prompt_contract_hash"]
        assert finding["category"] == case["expected_category"]
        assert finding["suggested_next_step"] == case["expected_next_step"]
        assert finding["confidence"] >= case["minimum_confidence"]
        assert set(finding["evidence_ids"]).issubset(evidence_ids)
        assert set(case["required_sources"]).issubset(source_types)


def test_golden_cases_are_versioned_with_the_active_prompt() -> None:
    assert {case["prompt_version"] for case in CASES} == {InvestigationService.PROMPT_VERSION}
    assert {case["prompt_contract_hash"] for case in CASES} == {InvestigationService.PROMPT_CONTRACT_HASH}


def test_small_analyzer_change_is_safe_and_cited() -> None:
    class QueueEvidenceProvider(SimulatorService):
        def query_evidence(self, source_type):
            response = super().query_evidence(source_type)
            if source_type == "metrics":
                response["items"] = [{"name": "queue_depth", "value": 120, "threshold": 20}]
            return response

    service = InvestigationService(
        Incident("orders-worker"),
        QueueEvidenceProvider(),
        MemoryRepository(),
        model_gateway=UnavailableModelGateway(),
    )
    result = service.investigate(UUID(int=10), "disk_pressure")

    assert result["findings"][0]["category"] == "queue_pressure"
    assert result["findings"][0]["suggested_next_step"] == "scale"
    assert set(result["findings"][0]["evidence_ids"]).issubset({item["id"] for item in result["evidence"]})

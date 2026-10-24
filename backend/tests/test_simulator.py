from fastapi.testclient import TestClient
from pathlib import Path
import pytest

from app.domain.simulator import SimulatorService
from app.main import app
from app.api import simulator as simulator_api


client = TestClient(app)


def test_scenarios_hide_root_causes() -> None:
    response = client.get("/api/v1/simulator/scenarios")

    assert response.status_code == 200
    assert len(response.json()) == 3
    assert all("hidden_cause" not in scenario for scenario in response.json())


def test_scenario_exposes_evidence_and_verifies_timeout() -> None:
    selected = client.post(
        "/api/v1/simulator/scenarios",
        json={"scenario_id": "deployment_regression"},
    )
    assert selected.status_code == 200

    evidence = client.get("/api/v1/simulator/evidence?source_type=deploys")
    assert evidence.status_code == 200
    assert evidence.json()["items"][0]["version"] == "2026.10.22"

    action = client.post(
        "/api/v1/simulator/actions",
        json={"action_type": "rollback", "target": "payments-api"},
    )
    assert action.status_code == 200
    action_body = action.json()
    assert action_body["status"] == "timed_out"
    assert action_body["verified"] is False
    assert action_body["state_before"]["version"] == "2026.10.22"
    assert action_body["state_after"]["version"] == "2026.10.21"

    verified = client.post(f"/api/v1/simulator/actions/{action_body['id']}/verify")
    assert verified.status_code == 200
    assert verified.json()["verified"] is True


def test_ecommerce_scenario_evidence_contains_operational_context() -> None:
    service = SimulatorService()
    service.select_scenario("deployment_regression")

    logs = service.query_evidence("logs")["items"][0]
    metrics = service.query_evidence("metrics")["items"][0]
    deploy = service.query_evidence("deploys")["items"][0]

    assert logs["trace_id"] == "pay-7f31"
    assert metrics["route"] == "/v1/payments/authorize"
    assert deploy["changed"] == ["payment repository query"]


def test_simulator_state_and_action_idempotency_survive_service_restart(tmp_path: Path) -> None:
    state_path = str(tmp_path / "simulator.json")
    first = SimulatorService(state_path)
    first.select_scenario("disk_pressure")
    action = first.execute_action("clear_disk", "orders-worker", {}, "clear-1")

    restarted = SimulatorService(state_path)
    assert restarted.state()["service_state"]["disk_usage_percent"] == 62
    assert restarted.execute_action("clear_disk", "orders-worker", {}, "clear-1")["id"] == action["id"]


def test_alert_delivery_controls_make_ordering_and_delay_visible() -> None:
    service = SimulatorService()
    service.select_scenario("deployment_regression")

    result = service.trigger_alert(None, 2, False, True, out_of_order=True, delayed_seconds=3)

    assert [item["lifecycle"] for item in result["deliveries"]] == ["resolved", "resolved", "firing", "firing"]
    assert len({item["source_event_id"] for item in result["deliveries"]}) == 2
    assert result["deliveries"][0]["source_time"] > result["deliveries"][-1]["source_time"]
    assert all(item["received_time"] > item["source_time"] for item in result["deliveries"])


def test_simulator_delivery_contains_a_webhook_ready_payload() -> None:
    service = SimulatorService()
    service.select_scenario("disk_pressure")

    delivery = service.trigger_alert(None, 1, False, False)["deliveries"][0]

    assert delivery["source"] == "simulator"
    assert delivery["labels"]["scenario"] == "disk_pressure"
    assert delivery["correlation_key"] == "disk_pressure"


def test_simulator_alert_endpoint_forwards_deliveries_to_incident_intake(monkeypatch) -> None:
    class FakeSimulator:
        def trigger_alert(self, *_args):
            return {"scenario_id": "disk_pressure", "deliveries": [{"source_event_id": "event-1"}]}

    accepted = []

    class FakePipeline:
        def accept(self, delivery):
            accepted.append(delivery)
            return {"duplicate": False, "incident": {"id": "incident-1"}}

    monkeypatch.setattr(simulator_api, "simulator_service", FakeSimulator())
    monkeypatch.setattr(simulator_api, "alert_pipeline_service", FakePipeline())

    response = client.post("/api/v1/simulator/alerts", json={"scenario_id": "disk_pressure"})

    assert response.status_code == 200
    assert response.json()["accepted"] == [{"duplicate": False, "incident": {"id": "incident-1"}}]
    assert accepted == [{"source_event_id": "event-1"}]


def test_failure_controls_are_visible_and_change_dependency_availability() -> None:
    service = SimulatorService()
    service.select_scenario("third_party_outage")
    assert service.state()["failure_controls"]["third_party_available"] is False

    evidence = service.query_evidence("service_health")
    assert evidence["availability"] == "unavailable"

    service.set_failure_controls(third_party_available=True)
    assert service.query_evidence("service_health")["availability"] == "available"


def test_action_validation_rejects_actions_not_allowed_by_scenario() -> None:
    service = SimulatorService()

    with pytest.raises(ValueError, match="not allowed"):
        service.validate_action("third_party_outage", "rollback", "checkout-api", {})

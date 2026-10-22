from fastapi.testclient import TestClient
from pathlib import Path

from app.domain.simulator import SimulatorService
from app.main import app


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
    assert all(item["received_time"] > item["source_time"] for item in result["deliveries"])


def test_failure_controls_are_visible_and_change_dependency_availability() -> None:
    service = SimulatorService()
    service.select_scenario("third_party_outage")
    assert service.state()["failure_controls"]["third_party_available"] is False

    evidence = service.query_evidence("service_health")
    assert evidence["availability"] == "unavailable"

    service.set_failure_controls(third_party_available=True)
    assert service.query_evidence("service_health")["availability"] == "available"

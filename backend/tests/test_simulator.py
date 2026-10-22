from fastapi.testclient import TestClient

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

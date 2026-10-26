from fastapi.testclient import TestClient

from app.application.observability import runtime_metrics
from app.main import app


def test_http_requests_return_and_record_a_bounded_request_id(monkeypatch) -> None:
    runtime_metrics.reset()
    response = TestClient(app).get("/api/v1/health", headers={"X-Request-ID": "ui-check-1"})

    assert response.status_code == 200
    assert response.headers["X-Request-ID"] == "ui-check-1"
    metrics = TestClient(app).get("/api/v1/metrics").json()
    health = next(row for row in metrics["routes"] if row["route"] == "/api/v1/health")
    assert health["status_class"] == "2xx"
    assert health["request_count"] == 1
    assert health["p95_ms"] >= 0


def test_invalid_request_id_is_replaced() -> None:
    response = TestClient(app).get("/api/v1/health", headers={"X-Request-ID": "bad value"})

    assert response.status_code == 200
    assert response.headers["X-Request-ID"] != "bad value"
    assert len(response.headers["X-Request-ID"]) == 32

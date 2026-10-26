import os
from datetime import datetime, timezone
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from fastapi import FastAPI, HTTPException


ON_CALL_API_URL = os.getenv("ON_CALL_API_URL", "http://localhost:8001").rstrip("/")

SCENARIO_PROFILES: dict[str, dict[str, Any]] = {
    "payments-api": {
        "dashboard_id": "payments-api",
        "name": "Payments API reliability",
        "description": "Release health, request latency, and checkout error pressure.",
        "metrics": [
            {"id": "request-latency", "label": "Request latency", "unit": "ms", "before": 3210, "after": 850, "direction": "lower", "target": "< 1000 ms", "points": [920, 1210, 1680, 3210, 2140, 1320, 850]},
            {"id": "error-rate", "label": "Error rate", "unit": "%", "before": 4.8, "after": 0.7, "direction": "lower", "target": "< 1%", "points": [0.8, 1.2, 2.4, 4.8, 3.2, 1.4, 0.7]},
            {"id": "cpu-usage", "label": "CPU usage", "unit": "%", "before": 78, "after": 54, "direction": "lower", "target": "< 70%", "points": [55, 58, 64, 78, 72, 61, 54]},
            {"id": "memory-usage", "label": "Memory usage", "unit": "%", "before": 74, "after": 71, "direction": "lower", "target": "< 80%", "points": [70, 72, 73, 74, 75, 72, 71]},
        ],
    },
    "orders-worker": {
        "dashboard_id": "orders-worker",
        "name": "Orders worker capacity",
        "description": "Storage pressure, queue depth, and fulfillment processing health.",
        "metrics": [
            {"id": "disk-usage", "label": "Disk usage", "unit": "%", "before": 93, "after": 68, "direction": "lower", "target": "< 80%", "points": [68, 74, 81, 93, 88, 76, 68]},
            {"id": "queue-depth", "label": "Queue depth", "unit": "jobs", "before": 240, "after": 64, "direction": "lower", "target": "< 100 jobs", "points": [62, 80, 121, 240, 210, 118, 64]},
            {"id": "cpu-usage", "label": "CPU usage", "unit": "%", "before": 88, "after": 62, "direction": "lower", "target": "< 75%", "points": [62, 68, 74, 88, 82, 70, 62]},
            {"id": "memory-usage", "label": "Memory usage", "unit": "%", "before": 82, "after": 79, "direction": "lower", "target": "< 85%", "points": [79, 80, 81, 82, 83, 80, 79]},
        ],
    },
    "checkout-api": {
        "dashboard_id": "checkout-api",
        "name": "Checkout dependency health",
        "description": "Dependency availability, authorization failures, and request pressure.",
        "metrics": [
            {"id": "dependency-success", "label": "Dependency success", "unit": "%", "before": 22, "after": 22, "direction": "higher", "target": "> 99%", "points": [99, 96, 72, 22, 31, 26, 22]},
            {"id": "error-rate", "label": "Error rate", "unit": "%", "before": 18, "after": 18, "direction": "lower", "target": "< 1%", "points": [1, 3, 8, 18, 17, 18, 18]},
            {"id": "cpu-usage", "label": "CPU usage", "unit": "%", "before": 46, "after": 46, "direction": "lower", "target": "< 70%", "points": [44, 45, 46, 46, 47, 46, 46]},
            {"id": "memory-usage", "label": "Memory usage", "unit": "%", "before": 63, "after": 63, "direction": "lower", "target": "< 80%", "points": [62, 63, 64, 63, 64, 63, 63]},
        ],
    },
}


class UpstreamError(Exception):
    def __init__(self, status_code: int, message: str) -> None:
        self.status_code = status_code
        self.message = message


def _read_json(path: str) -> Any:
    request = Request(f"{ON_CALL_API_URL}{path}", headers={"Accept": "application/json"})
    try:
        with urlopen(request, timeout=2) as response:
            import json

            return json.loads(response.read())
    except HTTPError as error:
        raise UpstreamError(error.code, "incident service rejected the monitoring request") from error
    except (URLError, TimeoutError, OSError) as error:
        raise UpstreamError(503, "incident service is unavailable") from error


def _profile_for(service: str) -> dict[str, Any]:
    return SCENARIO_PROFILES.get(service, SCENARIO_PROFILES["payments-api"])


def dashboard_catalog() -> list[dict[str, Any]]:
    return [
        {
            "dashboard_id": profile["dashboard_id"],
            "service": service,
            "name": profile["name"],
            "description": profile["description"],
            "metric_count": len(profile["metrics"]),
        }
        for service, profile in SCENARIO_PROFILES.items()
    ]


def _metric_outcome(before: float, current: float, direction: str, state: str) -> str:
    if state == "external_dependency":
        return "blocked"
    if current == before:
        return "steady"
    improved = current < before if direction == "lower" else current > before
    return "improved" if improved else "regressed"


def build_snapshot(incident: dict[str, Any] | None, actions: list[dict[str, Any]]) -> dict[str, Any]:
    service = incident.get("service", "payments-api") if incident else "payments-api"
    profile = _profile_for(service)
    incident_status = incident.get("status", "sample") if incident else "sample"
    latest_action = actions[-1] if actions else None
    action_result = (latest_action or {}).get("result") or {}
    verified = (latest_action or {}).get("status") == "verified" or action_result.get("verified") is True
    state = "healthy" if incident_status == "resolved" or verified else "external_dependency" if incident_status == "unfixable" else "degraded"
    metrics = []
    for source in profile["metrics"]:
        before = source["before"]
        current = source["after"] if state == "healthy" else before
        metrics.append({
            "id": source["id"],
            "label": source["label"],
            "unit": source["unit"],
            "before": before,
            "current": current,
            "target": source["target"],
            "direction": source["direction"],
            "points": source["points"],
            "outcome": _metric_outcome(before, current, source["direction"], state),
        })
    return {
        "dashboard_id": profile["dashboard_id"],
        "name": profile["name"],
        "description": profile["description"],
        "service": service,
        "state": state,
        "incident": incident,
        "metrics": metrics,
        "action": {
            "status": (latest_action or {}).get("status", "not proposed"),
            "verification": "Persisted action result and a fresh service-state check" if verified else "Awaiting human verification",
        },
        "observed_at": datetime.now(timezone.utc).isoformat(),
        "links": {
            "incident": f"http://localhost:8000/?incident={incident['id']}#remediation-section" if incident else "http://localhost:8000",
            "store": "http://localhost:8003",
        },
    }


app = FastAPI(title="Demo Observability", version="0.1.0")


@app.get("/api/observability/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "demo-observability"}


@app.get("/api/observability/dashboards")
def dashboards() -> dict[str, Any]:
    return {"dashboards": dashboard_catalog()}


@app.get("/api/observability/dashboards/{dashboard_id}")
def dashboard(dashboard_id: str) -> dict[str, Any]:
    profile = next((item for item in SCENARIO_PROFILES.values() if item["dashboard_id"] == dashboard_id), None)
    if profile is None:
        raise HTTPException(status_code=404, detail="dashboard not found")
    return build_snapshot({"service": dashboard_id, "status": "sample"}, [])


@app.get("/api/observability/incidents/{incident_id}")
def incident_dashboard(incident_id: str) -> dict[str, Any]:
    try:
        incident = _read_json(f"/api/v1/incidents/{incident_id}")
    except UpstreamError as error:
        raise HTTPException(status_code=404 if error.status_code == 404 else 503, detail=error.message) from error
    try:
        actions = _read_json(f"/api/v1/incidents/{incident_id}/actions")
    except UpstreamError:
        actions = []
    return build_snapshot(incident, actions)

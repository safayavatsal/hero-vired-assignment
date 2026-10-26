from fastapi.testclient import TestClient

from app.application.kubernetes_analyzers import analyze_resources
from app.main import app


def test_analyzer_catalog_is_read_only_and_has_six_resource_analyzers() -> None:
    response = TestClient(app).get("/api/v1/kubernetes/analyzers")

    assert response.status_code == 200
    analyzers = response.json()["analyzers"]
    assert {item["name"] for item in analyzers} == {
        "pod", "deployment", "service", "event", "node", "persistent_volume_claim"
    }
    assert all(item["read_only"] for item in analyzers)


def test_analyze_reports_pod_and_deployment_failures() -> None:
    result = analyze_resources([
        {
            "apiVersion": "v1",
            "kind": "Pod",
            "metadata": {"name": "checkout-7f", "namespace": "shop", "labels": {"app": "checkout"}},
            "status": {"phase": "Running", "containerStatuses": [{"name": "api", "ready": False, "state": {"waiting": {"reason": "CrashLoopBackOff"}}}]},
        },
        {
            "apiVersion": "apps/v1",
            "kind": "Deployment",
            "metadata": {"name": "checkout", "namespace": "shop", "labels": {"app": "checkout"}},
            "spec": {"replicas": 3},
            "status": {"readyReplicas": 1, "conditions": [{"type": "Progressing", "status": "False", "reason": "ProgressDeadlineExceeded"}]},
        },
    ], namespace="shop", labels={"app": "checkout"})

    assert result["status"] == "problem_detected"
    assert result["problems"] == 3
    assert {finding["analyzer"] for finding in result["findings"]} == {"pod", "deployment"}
    assert all(finding["suggested_next_step"] for finding in result["findings"])


def test_resource_and_analyzer_filters_limit_analysis() -> None:
    result = analyze_resources([
        {"kind": "Pod", "metadata": {"name": "one", "namespace": "shop"}, "status": {"phase": "Pending"}},
        {"kind": "Pod", "metadata": {"name": "two", "namespace": "other"}, "status": {"phase": "Pending"}},
    ], namespace="shop", resource_name="one", analyzer_names=["pod"])

    assert result["resources_scanned"] == 1
    assert len(result["findings"]) == 1
    assert result["findings"][0]["name"] == "one"


def test_service_analyzer_reports_missing_endpoints() -> None:
    result = analyze_resources([{
        "kind": "Service",
        "metadata": {"name": "checkout", "namespace": "shop"},
        "spec": {"selector": {"app": "checkout"}},
        "status": {"endpoints": []},
    }], analyzer_names=["service"])

    assert result["findings"][0]["reason"] == "Service has no ready endpoints."


def test_event_analyzer_reports_warning_events() -> None:
    result = analyze_resources([{
        "kind": "Event",
        "metadata": {"name": "checkout-warning", "namespace": "shop"},
        "type": "Warning",
        "reason": "FailedScheduling",
        "message": "insufficient memory",
    }], analyzer_names=["event"])

    assert result["findings"][0]["suggested_next_step"] == "inspect_related_resource"


def test_node_analyzer_reports_pressure() -> None:
    result = analyze_resources([{
        "kind": "Node",
        "metadata": {"name": "node-1"},
        "status": {"conditions": [{"type": "DiskPressure", "status": "True", "message": "disk is full"}]},
    }], analyzer_names=["node"])

    assert result["findings"][0]["severity"] == "critical"


def test_persistent_volume_claim_analyzer_reports_unbound_claims() -> None:
    result = analyze_resources([{
        "kind": "PersistentVolumeClaim",
        "metadata": {"name": "checkout-data", "namespace": "shop"},
        "status": {"phase": "Pending"},
    }], analyzer_names=["persistent_volume_claim"])

    assert result["findings"][0]["suggested_next_step"] == "inspect_storage"


def test_unknown_analyzer_is_rejected_by_api() -> None:
    response = TestClient(app).post("/api/v1/kubernetes/analyze", json={"analyzers": ["unknown"]})

    assert response.status_code == 400
    assert response.json()["detail"] == "unknown analyzer: unknown"

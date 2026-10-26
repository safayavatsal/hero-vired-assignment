from app.main import build_snapshot, dashboard_catalog


def test_dashboard_catalog_covers_the_built_in_incident_shapes() -> None:
    dashboards = dashboard_catalog()

    assert {item["service"] for item in dashboards} == {"payments-api", "orders-worker", "checkout-api"}
    assert all(item["metric_count"] >= 4 for item in dashboards)


def test_resolved_incident_projects_improved_monitoring_values() -> None:
    snapshot = build_snapshot(
        {
            "id": "incident-1",
            "service": "payments-api",
            "summary": "Checkout latency increased after a payment service release.",
            "severity": "critical",
            "status": "resolved",
            "updated_at": "2026-10-26T12:00:00Z",
        },
        [{"status": "verified", "result": {"verified": True}}],
    )

    latency = next(item for item in snapshot["metrics"] if item["id"] == "request-latency")
    assert snapshot["state"] == "healthy"
    assert latency["current"] < latency["before"]
    assert latency["outcome"] == "improved"


def test_unfixable_incident_stays_blocked_without_claiming_improvement() -> None:
    snapshot = build_snapshot(
        {
            "id": "incident-2",
            "service": "checkout-api",
            "summary": "Checkout authorization dependency is unavailable.",
            "severity": "critical",
            "status": "unfixable",
            "updated_at": "2026-10-26T12:00:00Z",
        },
        [],
    )

    assert snapshot["state"] == "external_dependency"
    assert {item["outcome"] for item in snapshot["metrics"]} == {"blocked"}

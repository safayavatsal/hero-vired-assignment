# Current State And Review Guide

## Runtime surfaces

| Surface | Location | Port | Role |
| --- | --- | --- | --- |
| Main console | `main-app/frontend` | `8000` | Incident selection, evidence review, ownership, remediation, verification, and explicit closure |
| Main API | `main-app/backend` | `8001` | Alert intake, incident state, investigation reads, workflow mutations, simulator access, and request metrics |
| Main worker | `main-app/backend/app/execution/worker.py` | Compose internal | Durable investigation, action, verification, retry, lease, and overdue-page work |
| Demo store | `demo-store/frontend`, `demo-store/backend` | `8003`, `8004` | Customer-facing checkout and controlled incident-producing journeys |
| Demo observability | `demo-observability/frontend`, `demo-observability/backend` | `8005`, `8006` | Read-only service dashboards with before/current values and incident backlinks |
| PostgreSQL | Compose service | Internal only | Incidents, evidence, findings, embeddings, jobs, workflow state, telemetry, and timeline history |

## Investigation boundary

The worker always runs the four fixed evidence tools and derives the deterministic finding first. Similar-history retrieval is a fifth evidence source and is unavailable until at least two completed findings exist. A configured model can request only allowlisted re-queries under bounded rounds, requests, evidence items, and wall-clock time. A missing or degraded model leaves the deterministic path intact.

## Operator boundary

The console reveals the finding category and recommended action only after investigation. The operator can notify an owner or claim ownership locally, approve and queue one typed action, inspect persistent before/after state, request verification, review the verification thesis and monitoring link, and close the incident explicitly.

## Review order

1. Read `_plan_docs/_hld_docs/00-system-architecture.md` for runtime ownership and data boundaries.
2. Read `_plan_docs/_hld_docs/02-main-ui-architecture.md` for the operator surface.
3. Read `_plan_docs/_lld_docs/00-lld-overview.md` and `_plan_docs/_lld_docs/06-lld-system-diagram.md` for package and class connections.
4. Open `_plan_docs/_hld_docs/08-main-product-architecture.html` for the rendered architecture map.
5. Use `DEMO_GUIDE.md` and `SCENARIO_RUNBOOK.md` for local execution and verification.

## Authority

This folder is a dated navigation and handoff packet. The feature plans, HLD, LLD, decision records, tests, and source code are the current authority.

# Hero Vired Assignment

Documentation-first implementation of an incident investigation and response product.

## Product flow

`alert -> incident -> evidence -> finding -> page -> approved action -> execution -> verification -> timeline`

The product accepts normalized alerts, groups repeat deliveries, collects bounded evidence, produces deterministic findings, optionally enriches them through a configured model gateway, pages responders, and requires explicit approval before an action is executed.

## Current capabilities

- Three deterministic scenarios: deployment regression, disk pressure, and third-party outage.
- Simulator alert deliveries are forwarded through the same incident webhook pipeline used by external alert sources, so a clean demo creates real incidents.
- PostgreSQL-backed incidents, alerts, evidence, findings, pages, actions, jobs, attempts, and timeline events.
- Worker-backed investigation and action execution with retry, lease, timeout, and recovery handling.
- Human paging, acknowledgement, free-form reply, fallback escalation, approval, rejection, execution, and verification.
- React incident console with stable selection, investigation controls, evidence review, action state, and timeline context.
- Browser-based demo store with catalog, cart, synthetic checkout, a controlled payment failure, an embedded observer, and a captured responder inbox.
- Local HTTP boundary tests for model, notification, ownership, and action reconciliation integrations.

## Repository map

- `_plan_docs/_features_docs/` — feature plans (00–17)
- `_plan_docs/_hld_docs/` — architecture, data model, UI, and API plans
- `_plan_docs/_lld_docs/` — classes, runtime sequence, and UML
- `_decision_docs/` — architecture and implementation decisions
- `_research_refs/` — assignment and research material
- `frontend/src/app/` — React screen and workflow orchestration
- `frontend/src/domain/` — shared frontend data types
- `frontend/src/lib/` — small reusable workflow helpers
- `frontend/src/styles/` — frontend presentation styles
- `demo-store/backend/` — synthetic catalog, payment router, and bounded alert adapter
- `demo-store/frontend/` — standalone customer-facing store and checkout
- `demo-output/` — local browser-only Kubernetes demo recordings

## Run locally

```bash
cp .env.example .env
docker compose up --build
```

- Frontend: `http://localhost:8000`
- Demo store: `http://localhost:8003`
- Demo store API: `http://localhost:8004/api/store/health`
- Backend liveness: `http://localhost:8001/api/v1/health`
- Backend readiness: `http://localhost:8001/api/v1/readiness`
- Responder inbox: `http://localhost:8002`

The API applies migrations before serving traffic. Credentials remain in the ignored `.env` file.

## Verify locally

```bash
docker compose config -q
docker compose run --rm --user root api pytest -q tests
(cd frontend && npm test && npm run build)
(cd demo-store/frontend && npm run build)
docker compose run --rm --user root store-backend pytest -q tests
./scripts/reset-demo.sh
./scripts/demo.sh
./scripts/verify-commerce-demo.sh
```

The demo exercises all scenarios with duplicate, late, flapping, delayed, and out-of-order deliveries, then shows degraded dependency evidence.

`verify-commerce-demo.sh` proves the approved checkout, declined checkout, incident creation, completed investigation, responder page, and captured inbox message against the running stack.

To create a fresh incident from the simulator, select a scenario and trigger its alert delivery:

```bash
curl -sS -X POST http://localhost:8001/api/v1/simulator/scenarios \
  -H 'content-type: application/json' \
  -d '{"scenario_id":"disk_pressure"}' >/dev/null
curl -sS -X POST http://localhost:8001/api/v1/simulator/alerts \
  -H 'content-type: application/json' \
  -d '{"scenario_id":"disk_pressure"}'
```

The response contains both the generated deliveries and the incidents accepted by the webhook pipeline. Refresh the UI on port `8000` to continue the investigation workflow.

### Add a new scenario live

New scenarios are data, not code. Send one definition to the scenario endpoint and the system investigates it immediately; registered scenarios survive restarts and appear in the console automatically:

```bash
curl -sS -X POST http://localhost:8001/api/v1/simulator/scenarios \
  -H 'content-type: application/json' \
  -d '{
    "scenario_id": "cache_stampede",
    "definition": {
      "name": "Cache stampede",
      "service": "catalog-api",
      "severity": "high",
      "alert_type": "cache_miss_rate_high",
      "hidden_cause": "cache expiry aligned with a traffic spike",
      "evidence": {
        "logs": [{"message": "cache miss storm on catalog lookups", "level": "error"}],
        "metrics": [{"name": "cache_miss_rate", "value": 82, "threshold": 20, "window": "5m"}],
        "deploys": [],
        "service_health": [{"service": "catalog-api", "healthy": true}]
      },
      "allowed_actions": ["restart"],
      "initial_state": {"cache_miss_rate": 82},
      "finding": {
        "metric": "cache_miss_rate",
        "category": "cache_stampede",
        "statement": "Cache misses spiked above threshold across the catalog service.",
        "confidence": 0.88,
        "suggested_next_step": "restart",
        "evidence_sources": ["metrics", "logs"]
      }
    }
  }'
```

Trigger its alerts with `{"scenario_id":"cache_stampede"}` against `/api/v1/simulator/alerts`, then investigate the new incident from the console.

For the presenter-facing commerce flow, open port `8003`, add a product, and use the displayed declined test card. The separate store backend validates the synthetic payment and its embedded observer sends only operational metadata to the normal alert endpoint. The customer sees a payment reference, not an internal incident link. In a separate operator-console tab, locate the new checkout incident, run the investigation, page the service owner, and open the responder inbox on port `8002` to show the captured notification. The approved test card completes without creating an incident.

The investigation view uses realistic e-commerce signals rather than a single generic fixture message. It records named bounded evidence queries and safe model telemetry, then shows the structured model readout separately from the deterministic finding. A configured model gateway can supply the structured analysis; without one, the deterministic finding remains visible with an explicit degraded model status.

## Verify on local Kubernetes

OrbStack Kubernetes can run the same images without a hosted deployment:

```bash
docker compose build api worker frontend store-backend store-frontend
kubectl apply -f k8s/local.yaml
kubectl -n hero-vired rollout status deployment/db --timeout=120s
kubectl -n hero-vired rollout status deployment/api --timeout=120s
kubectl -n hero-vired rollout status deployment/worker --timeout=120s
kubectl -n hero-vired rollout status deployment/frontend --timeout=120s
kubectl -n hero-vired rollout status deployment/store-backend --timeout=120s
kubectl -n hero-vired rollout status deployment/store-frontend --timeout=120s
kubectl -n hero-vired port-forward service/frontend 8000:8080
```

The Kubernetes UI uses the same frontend port (`8000`), and the frontend proxies API calls to the in-cluster `api` service. For direct API checks, use a second terminal:

```bash
kubectl -n hero-vired port-forward service/api 8001:8000
curl -sS http://localhost:8001/api/v1/readiness
```

For the store, forward its two services in separate terminals:

```bash
kubectl -n hero-vired port-forward service/store-frontend 8003:8080
kubectl -n hero-vired port-forward service/store-backend 8004:8000
kubectl -n hero-vired port-forward service/mailpit 8002:8025
```

## Start with the design

- [Feature baseline](_plan_docs/_features_docs/00-feature-baseline.md)
- [System architecture](_plan_docs/_hld_docs/00-system-architecture.md)
- [API catalog](_plan_docs/_hld_docs/03-api-catalog.md)
- [LLD overview](_plan_docs/_lld_docs/00-lld-overview.md)
- [UML class diagram](_plan_docs/_lld_docs/06-lld-system-diagram.md)
- [Scenario runbook](SCENARIO_RUNBOOK.md)
- [Demo guide](DEMO_GUIDE.md)

# Hero Vired Assignment

Documentation-first implementation of an incident investigation and response product.

## Product flow

`alert -> incident -> evidence -> finding -> page -> approved action -> execution -> verification -> timeline`

The product accepts normalized alerts, groups repeat deliveries, collects bounded evidence, produces deterministic findings, optionally enriches them through a configured model gateway, pages responders, and requires explicit approval before an action is executed.

## Current capabilities

- Three deterministic scenarios: deployment regression, disk pressure, and third-party outage.
- Simulator alert deliveries are forwarded through the same incident webhook pipeline used by external alert sources, so a clean demo creates real incidents.
- PostgreSQL-backed incidents, alerts, evidence, findings, pages, actions, jobs, attempts, and timeline events.
- Read-only queue metrics for pending, leased, retrying, succeeded, and dead-lettered work.
- Bounded HTTP request correlation and local route metrics at `GET /api/v1/metrics`.
- Worker-backed investigation and action execution with retry, lease, timeout, and recovery handling.
- Human paging, acknowledgement, free-form reply, fallback escalation, approval, rejection, execution, and verification.
- Scenario-owned investigation checklists that show the bounded checks before, during, and after a worker-backed investigation.
- Read-only evidence-tool catalog with named purposes, availability, timing, and persisted trace metadata.
- Read-only resource analyzer API with six named analyzers for Pods, Deployments, Services, Events, Nodes, and PersistentVolumeClaims, plus namespace, kind, name, label, and analyzer filters.
- Incident console with separate `Incidents` and `Kubernetes health` tabs; the health view has a runnable sample snapshot, finding cards, problem counts, and an explicit no-cluster-changes boundary.
- React incident console with stable selection, investigation controls, evidence review, action state, and timeline context.
- Browser-based demo store with catalog, cart, synthetic checkout, customer-facing slow-checkout and delayed-fulfillment journeys, a controlled payment failure, an embedded observer, and a captured responder inbox.
- Separate demo observability pages with service-specific synthetic metrics, before/current comparisons, and incident backlinks on ports `8005` and `8006`.
- Local HTTP boundary tests for model, notification, ownership, and action reconciliation integrations.

## Repository map

- `_plan_docs/_features_docs/` — feature plans (00–18)
- `_plan_docs/_hld_docs/` — architecture, data model, UI, and API plans
- `_plan_docs/_lld_docs/` — classes, runtime sequence, and UML
- `_decision_docs/` — architecture and implementation decisions
- `_research_refs/` — assignment and research material
- `main-app/frontend/src/app/` — React screen and workflow orchestration
- `main-app/frontend/src/domain/` — shared frontend data types
- `main-app/frontend/src/lib/` — small reusable workflow helpers
- `main-app/frontend/src/styles/` — frontend presentation styles
- `demo-store/backend/` — synthetic catalog, payment router, and bounded alert adapter
- `demo-store/frontend/` — standalone customer-facing store and checkout
- `demo-observability/backend/` and `demo-observability/frontend/` — read-only local monitoring demo
- `demo-output/` — local browser-only Kubernetes demo recordings

## Run locally

```bash
cp .env.example .env
docker compose up --build
```

- Frontend: `http://localhost:8000`
- Demo store: `http://localhost:8003`
- Demo store API: `http://localhost:8004/api/store/health`
- Demo observability: `http://localhost:8005`
- Demo observability API: `http://localhost:8006/api/observability/health`
- Backend liveness: `http://localhost:8001/api/v1/health`
- Backend readiness: `http://localhost:8001/api/v1/readiness`
- Responder inbox: `http://localhost:8002`

The API applies migrations before serving traffic. Credentials remain in the ignored `.env` file.

The resource analyzer surface is available without authentication for local snapshots:

```bash
curl http://localhost:8001/api/v1/kubernetes/analyzers
curl -X POST http://localhost:8001/api/v1/kubernetes/analyze \
  -H 'content-type: application/json' \
  -d '{"namespace":"shop","resources":[{"kind":"Pod","metadata":{"name":"checkout","namespace":"shop"},"status":{"phase":"Pending"}}]}'
```

It is read-only: findings recommend the next inspection step but do not change a resource.

The console also exposes this locally at the bottom of the incident view. Click `Run sample scan` to demonstrate a Pending pod and unhealthy deployment snapshot without needing a live cluster.

## Verify locally

```bash
docker compose config -q
docker compose run --rm --user root api pytest -q tests
(cd main-app/frontend && npm test && npm run build)
(cd demo-store/frontend && npm run build)
(cd demo-observability/frontend && npm test && npm run build)
docker compose run --rm demo-observability-backend pytest -q tests
docker compose run --rm --user root store-backend pytest -q tests
./scripts/verify-submission.sh
./scripts/reset-demo.sh
./scripts/demo.sh
./scripts/verify-commerce-demo.sh
curl http://localhost:8001/api/v1/jobs/metrics
curl http://localhost:8001/api/v1/metrics
./scripts/benchmark-queue.py --count 20
```

The demo exercises all scenarios with duplicate, late, flapping, delayed, and out-of-order deliveries, then shows degraded dependency evidence.

`verify-submission.sh` is the final local preflight. Run it after the Compose stack is up; it checks configuration, readiness, both served frontends, the demo-store proxy, both backend test suites, both frontend builds, the commerce workflow, and the working-tree diff.

`benchmark-queue.py` measures bounded work on the default durable queue and reports completion, elapsed time, throughput, and persisted queue metrics. It is an evaluation tool, not a required runtime dependency.

`verify-commerce-demo.sh` proves the approved checkout, declined checkout, incident creation, completed investigation, responder page, and captured inbox message against the running stack.

To create a fresh incident from the simulator, select a scenario for the synthetic alert delivery:

```bash
curl -sS -X POST http://localhost:8001/api/v1/simulator/scenarios \
  -H 'content-type: application/json' \
  -d '{"scenario_id":"disk_pressure"}' >/dev/null
curl -sS -X POST http://localhost:8001/api/v1/simulator/alerts \
  -H 'content-type: application/json' \
  -d '{"scenario_id":"disk_pressure"}'
```

The response contains both the generated deliveries and the incidents accepted by the webhook pipeline. Refresh the UI on port `8000`; the matching investigation context is selected automatically from the incident service.

### Add a new scenario live

New scenarios are data, not code. Send one definition to the scenario endpoint and the system investigates it immediately; registered scenarios survive restarts and appear in the console automatically:

For the validated register-and-trigger workflow, use the [scenario onboarding guide](docs/scenario-onboarding.md) and `./scripts/add-scenario.sh <definition.json>`.

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

For the presenter-facing commerce flow, open port `8003`, add a product, and use the `Demo journeys` section to try slow checkout, delayed fulfillment, and provider-unavailable checkout. The separate store backend sends only bounded operational metadata to the normal alert endpoint. The customer sees a safe reference, not an internal incident link. In a separate operator-console tab, locate each resulting incident, confirm its automatically selected investigation context, run the investigation, notify the service owner, and open the responder inbox on port `8002` to show the captured notification. The approved test card completes without creating an incident.

The investigation view uses realistic e-commerce signals rather than a single generic fixture message. It records named bounded evidence queries and safe model telemetry, then shows the structured model readout separately from the deterministic finding. Set `MODEL_GATEWAY_MODE=local` for a no-secret contract-valid model readout; a configured remote gateway remains optional, and without either the deterministic finding remains visible with an explicit degraded model status.

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

### Helm extension

The same local runtime is also packaged as an additive Helm chart. Build the local images, install the chart, and inspect the rollout:

```bash
docker compose build api worker frontend store-backend store-frontend
helm upgrade --install hero-vired ./k8s/helm/hero-vired \
  --namespace hero-vired --create-namespace
kubectl -n hero-vired get pods
helm test hero-vired --namespace hero-vired
```

Use the port-forward commands printed by Helm, or run the same forwards above. The chart defaults to local images and persistence; override `values.yaml` for credentials or registry-backed images. This is a local Kubernetes extension, not a hosted deployment path.

## Start with the design

- [Feature baseline](_plan_docs/_features_docs/00-feature-baseline.md)
- [System architecture](_plan_docs/_hld_docs/00-system-architecture.md)
- [Explorable main-product architecture](_plan_docs/_hld_docs/08-main-product-architecture.html)
- [API catalog](_plan_docs/_hld_docs/03-api-catalog.md)
- [LLD overview](_plan_docs/_lld_docs/00-lld-overview.md)
- [UML class diagram](_plan_docs/_lld_docs/06-lld-system-diagram.md)
- [Scenario runbook](SCENARIO_RUNBOOK.md)
- [Demo guide](DEMO_GUIDE.md)

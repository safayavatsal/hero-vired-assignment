# Demo Commerce Feature Map

## Feature boundaries

| Feature | Entry point | Core files | Purpose |
| --- | --- | --- | --- |
| Demo storefront | `demo-store/frontend/src/main.tsx` | `demo-store/frontend/src/App.tsx` | Browse a small catalog, enter synthetic payment details, and produce an approved or failed payment result. |
| Demo store API | `demo-store/backend/app/main.py` | `PaymentRequest`, `PaymentService`, `AlertGateway` | Own product pricing and synthetic payment behavior, then emit a bounded operational alert after a declined payment. |
| Alert intake | `POST /api/v1/alerts` | `main-app/backend/app/api/incidents.py`, `main-app/backend/app/application/alert_pipeline.py` | Validate, normalize, deduplicate, correlate, and persist a payment-failure alert. |
| Investigation workflow | `POST /api/v1/incidents/{id}/investigate` | `main-app/backend/app/application/investigation.py`, `main-app/backend/app/domain/simulator.py` | Collect scenario evidence and produce a cited finding. |
| Similar-history retrieval | Fifth evidence source | `main-app/backend/app/application/retrieval.py`, `main-app/backend/app/adapters/postgres_retrieval_repository.py` | Rank completed findings with deterministic local vectors while leaving the deterministic finding unchanged. |
| Bounded evidence loop | Optional configured-model enrichment | `main-app/backend/app/application/investigation.py`, `main-app/backend/app/application/model_gateway.py` | Validate and execute only allowlisted re-queries within round, item, request, and wall-clock limits. |
| Investigation telemetry | Persisted model and source timing | `main-app/backend/app/application/investigation.py`, `main-app/backend/app/application/observability.py` | Record token estimates, finite cost estimates, source durations, retrieval latency, and request metrics. |
| Responder delivery | `POST /api/v1/incidents/{id}/page` | `main-app/backend/app/application/workflow.py`, `main-app/backend/app/application/external_boundaries.py` | Attach the finding to a durable page and deliver a local responder notification. |
| Human-owned remediation | `POST /api/v1/incidents/{id}/actions/*` | `main-app/backend/app/application/workflow.py`, `main-app/frontend/src/app/App.tsx` | Keep ownership, approval, queueing, verification, before/after evidence, and closure explicit. |
| Scenario onboarding | `scripts/add-scenario.sh <definition.json>` | `scripts/add-scenario.sh`, `main-app/backend/app/api/simulator.py`, `main-app/backend/app/domain/simulator.py` | Register a validated data-defined scenario, trigger one alert, and print its incident id. |
| Operator console | `main-app/frontend/src/app/App.tsx` | `main-app/frontend/src/domain/types.ts`, `main-app/frontend/src/lib/incidentSelection.js` | Guide the operator through investigation, response, and safe action handling. |
| Demo observability | `http://localhost:8005` | `demo-observability/frontend/src/App.tsx`, `demo-observability/backend/app/main.py` | Show read-only service metrics, before/current outcomes, verification state, and incident backlinks. |

## Boundary decision

The store API emits the same canonical alert as any monitored application. It does not write incident tables, trigger an action, or bypass the evidence-first paging flow. Synthetic payment details cross only the store boundary and never enter alert payloads or persisted evidence. Scenario onboarding uses the same simulator and alert boundaries, while similar history, model enrichment, telemetry, and observability remain bounded supporting paths around the primary incident workflow.

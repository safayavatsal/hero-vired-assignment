# Demo Commerce Feature Map

## Feature boundaries

| Feature | Entry point | Core files | Purpose |
| --- | --- | --- | --- |
| Demo storefront | `demo-store/frontend/src/main.tsx` | `demo-store/frontend/src/App.tsx` | Browse a small catalog, enter synthetic payment details, and produce an approved or failed payment result. |
| Demo store API | `demo-store/backend/app/main.py` | `PaymentRequest`, `PaymentService`, `AlertGateway` | Own product pricing and synthetic payment behavior, then emit a bounded operational alert after a declined payment. |
| Alert intake | `POST /api/v1/alerts` | `main-app/backend/app/api/incidents.py`, `main-app/backend/app/application/alert_pipeline.py` | Validate, normalize, deduplicate, correlate, and persist a payment-failure alert. |
| Investigation workflow | `POST /api/v1/incidents/{id}/investigate` | `main-app/backend/app/application/investigation.py`, `main-app/backend/app/domain/simulator.py` | Collect scenario evidence and produce a cited finding. |
| Responder delivery | `POST /api/v1/incidents/{id}/page` | `main-app/backend/app/application/workflow.py`, `main-app/backend/app/application/external_boundaries.py` | Attach the finding to a durable page and deliver a local responder notification. |
| Operator console | `main-app/frontend/src/app/App.tsx` | `main-app/frontend/src/domain/types.ts`, `main-app/frontend/src/lib/incidentSelection.js` | Guide the operator through investigation, response, and safe action handling. |

## Boundary decision

The store API emits the same canonical webhook as any monitored application. It does not write incident tables, trigger an action, or bypass the evidence-first paging flow. Synthetic payment details cross only the store boundary and never enter alert payloads or persisted evidence.

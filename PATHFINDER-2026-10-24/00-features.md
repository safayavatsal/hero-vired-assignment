# Demo Commerce Feature Map

## Feature boundaries

| Feature | Entry point | Core files | Purpose |
| --- | --- | --- | --- |
| Demo storefront | `frontend/src/main.tsx` | `frontend/src/app/Storefront.tsx`, `frontend/src/lib/paymentFailureAlert.js` | Browse a small catalog, enter synthetic payment details, and produce an approved or failed payment result. |
| Alert intake | `POST /api/v1/alerts` | `backend/app/api/incidents.py`, `backend/app/application/alert_pipeline.py` | Validate, normalize, deduplicate, correlate, and persist a payment-failure alert. |
| Investigation workflow | `POST /api/v1/incidents/{id}/investigate` | `backend/app/application/investigation.py`, `backend/app/domain/simulator.py` | Collect scenario evidence and produce a cited finding. |
| Responder delivery | `POST /api/v1/incidents/{id}/page` | `backend/app/application/workflow.py`, `backend/app/application/external_boundaries.py` | Attach the finding to a durable page and deliver a local responder notification. |
| Operator console | `frontend/src/app/App.tsx` | `frontend/src/domain/types.ts`, `frontend/src/lib/incidentSelection.js` | Guide the operator through investigation, response, and safe action handling. |

## Boundary decision

The storefront emits the same canonical webhook as any monitored application. It does not write incident tables, trigger an action, or bypass the evidence-first paging flow. Synthetic card details remain in browser state and never enter alert payloads or persisted evidence.

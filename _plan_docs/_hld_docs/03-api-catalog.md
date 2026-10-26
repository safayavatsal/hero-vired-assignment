# API Catalog

This document lists the major HTTP APIs in the product. Detailed request validation and implementation behavior belong in the LLD.

## POST APIs

| Path | Responsibility |
| --- | --- |
| `/api/v1/alerts` | Accept and correlate an incoming alert idempotently |
| `/api/v1/incidents/{incident_id}/status` | Apply a validated incident state transition |
| `/api/v1/incidents/{incident_id}/investigate` | Collect bounded evidence and produce deterministic findings |
| `/api/v1/incidents/{incident_id}/page` | Deliver a durable primary responder page or create a local ownership claim |
| `/api/v1/pages/{page_id}/respond` | Acknowledge, reply to, or timeout a page |
| `/api/v1/incidents/{incident_id}/actions` | Create an approval-bound typed action proposal |
| `/api/v1/actions/{action_id}/decision` | Approve or reject a typed action |
| `/api/v1/actions/{action_id}/execute` | Execute an approved action through the simulator |
| `/api/v1/actions/{action_id}/verify` | Verify the persisted action outcome |
| `/api/v1/incidents/{incident_id}/close` | Explicitly close an incident after a verified action |
| `/api/v1/actions/{action_id}/reconcile` | Reconcile an unknown action through the configured external executor |
| `/api/v1/auth/context` | Return the authenticated local operator role without exposing credentials |
| `/api/v1/simulator/scenarios` | Add or select a deterministic simulator scenario |
| `/api/v1/simulator/alerts` | Trigger a simulator alert for a scenario |
| `/api/v1/simulator/reset` | Reset the selected simulator scenario |
| `/api/v1/simulator/actions` | Execute a permitted typed simulator action |
| `/api/v1/simulator/actions/{action_id}/verify` | Verify a simulator action outcome |
| `/api/store/payments` | Process a synthetic store payment and emit an operational alert for a controlled decline |

## GET APIs

| Path | Responsibility |
| --- | --- |
| `/api/v1/incidents` | List incidents with status, severity, service, and update time |
| `/api/v1/incidents/{incident_id}` | Return the incident detail read model |
| `/api/v1/incidents/{incident_id}/timeline` | Return ordered incident events |
| `/api/v1/incidents/{incident_id}/pages` | Return page delivery and response state |
| `/api/v1/incidents/{incident_id}/actions` | Return typed action proposal and execution state |
| `/api/v1/incidents/{incident_id}/evidence` | Return collected evidence and availability states |
| `/api/v1/investigation-tools` | List the fixed and historical evidence tools with purposes and enabled state |
| `/api/v1/jobs/metrics` | Return bounded queue counts and wait/processing timings |
| `/api/v1/metrics` | Return bounded in-process HTTP request counts and latency percentiles |
| `/api/v1/health` | Report API and dependency health |
| `/api/v1/simulator/scenarios` | List available simulator scenarios without hidden causes |
| `/api/v1/simulator/state` | Return selected scenario state and action records |
| `/api/v1/simulator/evidence` | Query logs, metrics, deploys, or service health |
| `/api/store/health` | Report demo-store backend health |
| `/api/store/products` | Return the deterministic demo product catalog |


## API rules

- All mutating endpoints accept an idempotency key where duplicate requests are possible.
- Human decisions return the updated incident state and the created timeline event.
- Action approval never executes an action inside the request handler; it creates durable work.
- A page request may include a validated recipient email or `notify=false` for a local ownership claim.
- The browser combines approval with the existing execute request so one operator action records approval and queueing; the execute route remains compatible for other clients.
- Verification records the action result but does not resolve the incident; the close endpoint requires a verified action and records the resolution event.
- Error responses expose safe problem details and never treat model or simulator text as trusted instructions.
- Similar-incident retrieval, bounded model re-queries, and telemetry are additive fields in the existing investigation response; no new investigation route is required.
- `scripts/add-scenario.sh` uses the existing scenario-registration and alert endpoints, then prints the accepted incident identifier.
- Queue metrics are read-only operational summaries and never include job payloads or error bodies.
- Operator mutations use the opt-in role boundary when `AUTH_MODE=required`; the default local demo remains unauthenticated by design.
- API responses return a bounded `X-Request-ID`; route-level metrics use fixed templates and status classes rather than raw URLs.

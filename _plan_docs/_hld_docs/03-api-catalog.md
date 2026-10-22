# API Catalog

This document lists the major HTTP APIs in the product. Detailed request validation and implementation behavior belong in the LLD.

## POST APIs

| Path | Responsibility |
| --- | --- |
| `/api/v1/alerts` | Accept and correlate an incoming alert idempotently |
| `/api/v1/incidents/{incident_id}/acknowledge` | Record human acknowledgement |
| `/api/v1/incidents/{incident_id}/reply` | Record a responder reply |
| `/api/v1/incidents/{incident_id}/actions/{action_id}/approve` | Approve a typed action |
| `/api/v1/incidents/{incident_id}/actions/{action_id}/reject` | Reject a typed action |
| `/api/v1/simulator/scenarios` | Add or select a deterministic simulator scenario |
| `/api/v1/simulator/alerts` | Trigger a simulator alert for a scenario |

## GET APIs

| Path | Responsibility |
| --- | --- |
| `/api/v1/incidents` | List incidents with status, severity, service, and update time |
| `/api/v1/incidents/{incident_id}` | Return the incident detail read model |
| `/api/v1/incidents/{incident_id}/timeline` | Return ordered incident events |
| `/api/v1/incidents/{incident_id}/evidence` | Return collected evidence and availability states |
| `/api/v1/incidents/{incident_id}/actions` | Return action requests, attempts, and verification |
| `/api/v1/health` | Report API and dependency health |


## API rules

- All mutating endpoints accept an idempotency key where duplicate requests are possible.
- Human decisions return the updated incident state and the created timeline event.
- Action approval never executes an action inside the request handler; it creates durable work.
- Error responses expose safe problem details and never treat model or simulator text as trusted instructions.

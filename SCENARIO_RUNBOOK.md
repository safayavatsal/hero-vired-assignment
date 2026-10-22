# Scenario Runbook

## Available scenarios

| Scenario | Service | Hidden cause exposed through |
| --- | --- | --- |
| `deployment_regression` | `payments-api` | Logs, metrics, and deployment history |
| `disk_pressure` | `orders-worker` | Logs, metrics, and service health |
| `third_party_outage` | `checkout-api` | Logs, metrics, and service health |

Select a scenario with:

```bash
curl -X POST http://localhost:8001/api/v1/simulator/scenarios \
  -H 'Content-Type: application/json' \
  -d '{"scenario_id":"deployment_regression"}'
```

The incident workflow now supports investigation, human paging, fallback escalation, typed action approval, simulator execution, verification, and timeline audit events.

For local restart checks, Compose stores simulator state at `/tmp/hero-vired-simulator-state.json` inside the API container. Alert simulation supports duplicate, late, flapping, delayed, and out-of-order deliveries. Action requests may include an `idempotency_key` so a repeated request returns the original action record.

The alert pipeline now accepts canonical webhook payloads at `POST /api/v1/alerts` and exposes incidents through `GET /api/v1/incidents`.

Incident and timeline records are persisted in PostgreSQL. Repeating an alert with the same `source_event_id` returns the existing record without adding a second alert or timeline event.

After creating an incident, run `POST /api/v1/incidents/<incident-id>/investigate` with a `scenario_id` whose service matches the incident. The request advances a received incident to `investigating`, records an `investigation_started` timeline event, and returns bounded evidence with a finding containing confidence, uncertainty, suggested next step, and cited evidence identifiers.

If the same incident and scenario are investigated after an API restart, the persisted investigation is returned instead of collecting and storing a second result.

For paging, call `POST /api/v1/incidents/<incident-id>/page`, then respond through `POST /api/v1/pages/<page-id>/respond`. Use `response_type=timeout` to exercise the fallback path; the primary page becomes `escalated` and one fallback page becomes `delivered`.

For actions, call `POST /api/v1/incidents/<incident-id>/actions`, approve through `POST /api/v1/actions/<action-id>/decision`, then execute and verify through the corresponding action endpoints. Reusing an idempotency key returns the existing proposal.

Verification evidence on 2026-10-22: the Docker/Postgres stack reached readiness, 24 backend tests passed, the frontend test/build checks passed, backend and frontend health checks returned HTTP 200, and the happy path produced one acknowledged page, one verified action, and persisted timeline events. The timeout path produced one escalated primary plus one delivered fallback with no duplicate on retry.

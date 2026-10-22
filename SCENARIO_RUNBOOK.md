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

The incident workflow that investigates and responds to these scenarios will be documented after those feature slices are implemented.

The alert pipeline now accepts canonical webhook payloads at `POST /api/v1/alerts` and exposes incidents through `GET /api/v1/incidents`.

Incident and timeline records are persisted in PostgreSQL. Repeating an alert with the same `source_event_id` returns the existing record without adding a second alert or timeline event.

After creating an incident, run `POST /api/v1/incidents/<incident-id>/investigate` with the selected `scenario_id`. The response contains bounded evidence records and a finding with confidence, uncertainty, suggested next step, and cited evidence identifiers.

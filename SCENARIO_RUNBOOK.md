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

For local restart checks, Compose stores simulator state at `/tmp/hero-vired-simulator-state.json` inside the API container. Alert simulation supports duplicate, late, flapping, delayed, and out-of-order deliveries. Action requests may include an `idempotency_key` so a repeated request returns the original action record.

The alert pipeline now accepts canonical webhook payloads at `POST /api/v1/alerts` and exposes incidents through `GET /api/v1/incidents`.

Incident and timeline records are persisted in PostgreSQL. Repeating an alert with the same `source_event_id` returns the existing record without adding a second alert or timeline event.

After creating an incident, run `POST /api/v1/incidents/<incident-id>/investigate` with the selected `scenario_id`. The response contains bounded evidence records and a finding with confidence, uncertainty, suggested next step, and cited evidence identifiers.

If the same incident and scenario are investigated after an API restart, the persisted investigation is returned instead of collecting and storing a second result.

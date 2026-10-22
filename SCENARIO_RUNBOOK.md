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

The incident workflow that consumes these scenarios will be documented after alert intake is implemented.

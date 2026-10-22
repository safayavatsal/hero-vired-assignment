# Demo Guide

## Baseline runtime

Run `docker compose up --build`, open `http://localhost:8000`, and confirm that the page reports the API as healthy.

The API endpoints are available at `http://localhost:8001/api/v1/health` and `http://localhost:8001/api/v1/readiness`.

List scenarios:

```bash
curl http://localhost:8001/api/v1/simulator/scenarios
```

Select a scenario and inspect its evidence:

```bash
curl -X POST http://localhost:8001/api/v1/simulator/scenarios \
  -H 'Content-Type: application/json' \
  -d '{"scenario_id":"deployment_regression"}'
curl 'http://localhost:8001/api/v1/simulator/evidence?source_type=deploys'
```

Trigger an alert:

```bash
curl -X POST http://localhost:8001/api/v1/simulator/alerts \
  -H 'Content-Type: application/json' \
  -d '{"duplicate_count":2,"late":true,"flapping":true}'
```

Incident scenarios will be added as later feature slices.

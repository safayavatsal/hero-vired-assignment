# Demo Guide

## Baseline runtime

Run `docker compose up --build`, open `http://localhost:8000`, and confirm that the page reports the API as healthy.

The API endpoints are available at `http://localhost:8001/api/v1/health` and `http://localhost:8001/api/v1/readiness`.

Optional model configuration:

```bash
cp .env.example .env
# Set MODEL_GATEWAY_URL and MODEL_GATEWAY_TOKEN in .env before starting Compose.
# For the Responses API adapter, also set MODEL_GATEWAY_FORMAT=openai_responses.
```

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

Submit an alert directly to the alert pipeline:

```bash
curl -X POST http://localhost:8001/api/v1/alerts \
  -H 'Content-Type: application/json' \
  -d '{"source_event_id":"event-1","source":"simulator","service":"payments-api","severity":"critical","alert_type":"p99_latency_high","source_time":"2026-10-22T12:00:00Z","labels":{"region":"primary"},"description":"p99 latency is above threshold","correlation_key":"payments-latency"}'
curl http://localhost:8001/api/v1/incidents
```

Move an incident into investigation after replacing `<incident-id>` with the returned identifier:

```bash
curl -X POST http://localhost:8001/api/v1/incidents/<incident-id>/status \
  -H 'Content-Type: application/json' \
  -d '{"target_status":"investigating"}'
```

Restart the API container and call `GET /api/v1/incidents` again to demonstrate that the incident data is loaded from PostgreSQL.

Run a bounded investigation for the selected scenario:

```bash
curl -X POST http://localhost:8001/api/v1/incidents/<incident-id>/investigate \
  -H 'Content-Type: application/json' \
  -d '{"scenario_id":"deployment_regression"}'
curl http://localhost:8001/api/v1/incidents/<incident-id>/evidence
```

Incident scenarios will be added as later feature slices.

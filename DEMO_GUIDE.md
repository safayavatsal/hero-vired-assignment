# Demo Guide

## Baseline runtime

Run `docker compose up --build`, open `http://localhost:8000`, and confirm that the incident console loads.

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

Restart the API container and call `GET /api/v1/incidents` again to demonstrate that the incident data is loaded from PostgreSQL.

Run a bounded investigation for the matching scenario. The API advances a received incident to `investigating` and records the investigation start in the timeline:

```bash
curl -X POST http://localhost:8001/api/v1/incidents/<incident-id>/investigate \
  -H 'Content-Type: application/json' \
  -d '{"scenario_id":"deployment_regression"}'
curl http://localhost:8001/api/v1/incidents/<incident-id>/evidence
```

## Paging and approved actions

After creating an incident, create and acknowledge a page:

```bash
curl -X POST http://localhost:8001/api/v1/incidents/<incident-id>/page \
  -H 'Content-Type: application/json' \
  -d '{"responder":"primary-oncall","fallback_responder":"secondary-oncall","deadline_seconds":300}'
curl -X POST http://localhost:8001/api/v1/pages/<page-id>/respond \
  -H 'Content-Type: application/json' \
  -d '{"response_type":"acknowledge","response_text":"Investigating"}'
curl http://localhost:8001/api/v1/incidents/<incident-id>/pages
```

Propose, approve, execute, and verify a typed action:

```bash
curl -X POST http://localhost:8001/api/v1/incidents/<incident-id>/actions \
  -H 'Content-Type: application/json' \
  -d '{"scenario_id":"deployment_regression","action_type":"rollback","target":"payments-api","parameters":{},"idempotency_key":"demo-action-1"}'
curl -X POST http://localhost:8001/api/v1/actions/<action-id>/decision \
  -H 'Content-Type: application/json' \
  -d '{"approved":true,"responder":"primary-oncall"}'
curl -X POST http://localhost:8001/api/v1/actions/<action-id>/execute
curl -X POST http://localhost:8001/api/v1/actions/<action-id>/verify
curl http://localhost:8001/api/v1/incidents/<incident-id>/actions
curl http://localhost:8001/api/v1/incidents/<incident-id>/timeline
```

The UI exposes the same page, investigation, evidence, and action controls after selecting an incident. Choose a scenario, select `Investigate`, then review the finding, confidence, uncertainty, citations, source availability, and masked evidence payloads. The live Docker verification covered acknowledgement, approval, simulator execution, verification, timeline persistence, fallback escalation, and retry safety.

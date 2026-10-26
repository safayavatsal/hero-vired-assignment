# Demo Guide

## Baseline runtime

Run `docker compose up --build`, open `http://localhost:8000`, and confirm that the incident console loads.

The API endpoints are available at `http://localhost:8001/api/v1/health` and `http://localhost:8001/api/v1/readiness`.

## Commerce-to-incident browser demo

1. Open `http://localhost:8003` and add any product to the cart.
2. Use `Try slow checkout` to create a customer-visible latency symptom and a `payments-api` incident.
3. Use `Try delayed fulfillment` to create a customer-visible fulfillment delay and an `orders-worker` incident.
4. Select `Open failed checkout`, choose `Use declined card`, and submit the synthetic payment.
5. Confirm the customer-safe failed payment result and its payment reference.
6. In a separate operator-console tab, locate any resulting incident and start the matching investigation.
7. Select `Page service owner`, then open `http://localhost:8002` to show the captured email with the incident, finding, and next step.

The incident console shows an investigation checklist for the selected scenario. Before starting, the four checks are pending; after `Start investigation`, they become active while the worker runs and complete when the finding is ready. This gives the presenter a visible explanation of what the system is checking.

For a resource-health demo, open the `Kubernetes health` tab and click `Run sample scan`. It shows a Pending pod, an unhealthy deployment, problem counts, read-only analyzer coverage, and suggested inspection steps. The API remains available through `GET /api/v1/kubernetes/analyzers` and `POST /api/v1/kubernetes/analyze` for custom snapshots and filters; no resource is changed.

Expand `Evidence used` and then `View tool trace` to show each bounded query's purpose, stable query name, availability, and duration. API clients can discover the same read-only catalog at `GET /api/v1/investigation-tools`.

For similar-history context, run the same scenario for two different incidents. The second completed investigation shows a `Similar past incidents` panel with the prior statement, category, and resolution. The first run reports that the history is not yet large enough; this is an uncertainty note and does not change the deterministic finding.

When a model gateway is configured, its optional evidence requests remain server-validated and bounded. The tool trace shows the extra read-only query, while the model telemetry records rejected requests and the loop stop reason. With no model configuration, only the fixed evidence path runs.

The same evidence panel shows prompt tokens, completion tokens, estimated cost, and the slowest evidence source. The cost is an estimate from local rate settings, not a billing record.

The checkout form talks to the separate demo-store backend on port `8004`. Its embedded observer emits bounded operational metadata only after the simulated provider becomes unavailable. Cardholder, card number, expiry, and security code are validated there but never persisted or copied into the event payload. Use `Use approved card` to demonstrate the non-incident path.

Before presenting, run the repeatable API-level proof:

```bash
./scripts/verify-commerce-demo.sh
```

It prints one compact JSON result containing the approved outcome, provider-failure investigation, delivered page, captured-message count, and fresh incident identifiers for the latency and fulfillment journeys.

For the final local submission check, run `./scripts/verify-submission.sh` after the stack is running. It combines both backend suites, served-frontend and demo-store proxy checks, frontend builds, health checks, commerce proof, and diff validation.

## Live scenario addition demo

New scenarios are registered as data through `POST /api/v1/simulator/scenarios` with a `definition` payload (see the README example). During a session:

For the shortest presenter path, prepare a definition JSON file and run `./scripts/add-scenario.sh <definition.json>`. It validates the payload, registers the scenario, triggers one alert, and prints the incident ID. The full file shape is in [Scenario onboarding](docs/scenario-onboarding.md).

1. Register the described scenario with its evidence, allowed actions, and finding rule.
2. Trigger its alert through `/api/v1/simulator/alerts`.
3. Investigate the new incident in the console; the scenario dropdown and action types follow the public scenario listing automatically.

Registered scenarios persist in simulator state, so a restart keeps them available. Built-in scenarios cannot be replaced and incomplete definitions are rejected.

## Local Kubernetes browser verification

OrbStack runs the same workflow with the local Kubernetes manifest:

```bash
docker compose build api worker frontend store-backend store-frontend
kubectl apply -f k8s/local.yaml
kubectl -n hero-vired rollout status deployment/db --timeout=120s
kubectl -n hero-vired rollout status deployment/api --timeout=120s
kubectl -n hero-vired rollout status deployment/worker --timeout=120s
kubectl -n hero-vired rollout status deployment/frontend --timeout=120s
kubectl -n hero-vired rollout status deployment/store-backend --timeout=120s
kubectl -n hero-vired rollout status deployment/store-frontend --timeout=120s
kubectl -n hero-vired port-forward service/frontend 8000:8080
kubectl -n hero-vired port-forward service/store-frontend 8003:8080
kubectl -n hero-vired port-forward service/store-backend 8004:8000
kubectl -n hero-vired port-forward service/mailpit 8002:8025
```

Open `http://localhost:8000` and run the same guided path: select an incident, start or repeat the matching investigation, page the owner, acknowledge, reply, propose the safe action, approve it, queue it, and verify the service state. The local browser pass confirmed the success toast after each transition and the worker result appearing in the selected incident.

The browser-only Kubernetes recordings are stored locally in `demo-output/`:

- `kubernetes-demo-workflow.mov` shows the incident console and live investigation feedback.
- `kubernetes-demo.mov` shows the completed guided workflow state.

## Helm browser verification

The Helm chart is an additive local deployment option:

```bash
docker compose build api worker frontend store-backend store-frontend
helm upgrade --install hero-vired ./k8s/helm/hero-vired --namespace hero-vired --create-namespace
kubectl -n hero-vired rollout status deployment/api --timeout=120s
helm test hero-vired --namespace hero-vired
kubectl -n hero-vired port-forward service/frontend 8000:8080
```

Open `http://localhost:8000`, run one guided incident workflow, and use the store and notification port-forwards from the Helm notes for the commerce path. The chart uses the same local images and service contracts as the raw manifest.

The workflow strip is sequential: investigation comes first, responder work unlocks after a finding, and action controls unlock after acknowledgement. `Verified` appears only after service-state verification succeeds.

For an in-cluster backend suite without pytest cache permission warnings:

```bash
kubectl -n hero-vired exec deployment/api -- env PYTEST_ADDOPTS='-p no:cacheprovider' pytest -q tests
```

Optional model configuration:

```bash
cp .env.example .env
# Set MODEL_GATEWAY_TOKEN and database credentials in .env before starting Compose.
# MODEL_GATEWAY_URL and MODEL_GATEWAY_FORMAT are optional provider overrides.
# MODEL_GATEWAY_MODEL selects the configured provider model shown in `.env.example`.
# The API applies backend migrations automatically during startup.
```

Feature 8 runtime bounds can be tuned in `.env`: `EVIDENCE_TIMEOUT_SECONDS`, `EVIDENCE_CONCURRENCY`, `MODEL_GATEWAY_TIMEOUT_SECONDS`, `MODEL_MAX_EVIDENCE_ITEMS`, `MODEL_MAX_PROMPT_BYTES`, `EXTERNAL_BOUNDARY_TIMEOUT_SECONDS`, and `JOB_RETRY_BACKOFF_SECONDS`. The defaults keep local investigations bounded and do not require a hosted deployment.

Run the deterministic evaluation cases:

```bash
docker compose run --rm --user root api pytest -q tests/test_evaluation.py
```

Run all scenarios and the degraded evidence path:

```bash
./scripts/demo.sh
./scripts/reset-demo.sh
```

The scripts use `BASE_URL` when set; otherwise they use the backend on port `8001`.

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

Queue a bounded investigation for the matching scenario. The API advances a received incident to `investigating`, records the investigation start in the timeline, and returns a durable queued job. The worker collects evidence and persists the completed result:

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
# The response is queued; the worker processes it and the action status becomes completed or timed_out.
curl -X POST http://localhost:8001/api/v1/actions/<action-id>/verify
curl http://localhost:8001/api/v1/incidents/<incident-id>/actions
curl http://localhost:8001/api/v1/incidents/<incident-id>/timeline
```

The UI exposes the same page, investigation, evidence, and action controls after selecting an incident. Confirm the automatically selected investigation context, start the investigation, then review the finding, confidence, uncertainty, citations, source availability, and masked evidence payloads. The `Change context` option is reserved for controlled demo runs. The live Docker verification covered acknowledgement, approval, simulator execution, verification, timeline persistence, fallback escalation, and retry safety.

For the UI walkthrough, select an incident and confirm its investigation context. Click `Start investigation`; the UI immediately confirms that the request was accepted and shows background progress. After the finding appears, use `Request deeper investigation` only when the result needs another evidence pass. The owner-notification step appears only after the finding is ready, closes after acknowledgement, and the remediation step then explains its evidence-backed recommendation before approval. Failures appear in the top-right toast and can be dismissed; the selected incident remains the source of truth for all controls.

### Five-minute live walkthrough

1. Open `http://localhost:8000` and select the first incident.
2. Read the `What happens next` strip aloud: find the cause, notify the owner, then approve and verify remediation.
3. Confirm the automatically selected investigation context, then click `Start investigation` or `Re-run investigation`. Point out the success toast and the background progress message; wait for the finding to appear.
4. Show the finding card: cause, confidence, recommended next step, and named evidence sources.
5. Open `Model readout` to show the three-part investigation brief, provider status, and response time. Open `Evidence used` only when you want to show the bounded tool trace and query timings.
6. Click `Notify service owner`, optionally send an owner note before acknowledgement, then click `Acknowledge ownership`. Explain that acknowledgement records human ownership; it does not resolve the incident.
7. After acknowledgement, review the recommended action, approve it, queue it, and click `Verify service state` after the worker updates the result. The incident then becomes `Resolved`.
8. Open `Audit trail` only when the audience wants the supporting detail; raw payloads remain opt-in.

For `third_party_outage`, complete investigation and paging but do not propose a local action. The UI marks the third step `No local fix`, and the incident becomes `Unfixable` with the reason preserved in the timeline.

For a failure demonstration, choose a mismatched scenario or reject an action. The UI keeps the normal page intact and shows the backend reason in a dismissible toast.

When an investigation is complete before paging, the delivered page also carries the finding summary and suggested next step to the notification boundary.

## Realistic e-commerce proof

Use the three built-in scenarios as a small e-commerce system: payment authorization latency, worker disk pressure, and checkout dependency failure. During the demo, point out the route, trace or provider, deployment, queue, and time-window fields in `Evidence used`; then open `Model readout` to show the structured condition, likely cause, next step, confidence, uncertainty, and citations. Keep raw payloads closed unless the audience asks for implementation detail.

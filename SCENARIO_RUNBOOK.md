# Scenario Runbook

## Scenario matrix

| Scenario | Service | Expected finding | Safe next step |
| --- | --- | --- | --- |
| `deployment_regression` | `payments-api` | Latency regression after a version change | `rollback` |
| `disk_pressure` | `orders-worker` | Disk usage is high and cleanup is degraded | `clear_disk` |
| `third_party_outage` | `checkout-api` | Dependency failures with degraded health evidence | `failover` |

## Customer-facing triggers

The standalone store at `http://localhost:8003` reproduces the same three scenarios without exposing operator controls:

| Store journey | Incident scenario | Customer-visible result |
| --- | --- | --- |
| `Try slow checkout` | `deployment_regression` | Checkout is taking longer than usual |
| `Try delayed fulfillment` | `disk_pressure` | Order accepted, fulfillment delayed |
| `Open failed checkout` with the declined test card | `third_party_outage` | Payment cannot be completed |

Each journey sends bounded operational metadata through the normal alert intake. The customer sees a safe reference; investigation, paging, and any approved action still happen in the separate operator console.

## Tester workflow

1. Start Compose and confirm `/api/v1/readiness` returns `{"status":"ready","database":"ok"}`.
2. Select one scenario with `POST /api/v1/simulator/scenarios`.
3. Generate deliveries with `POST /api/v1/simulator/alerts`.
4. Confirm duplicate deliveries do not create duplicate incidents or timeline events.
5. Investigate the matching incident and check evidence, finding, confidence, uncertainty, citations, and model status.
   For the e-commerce proof, confirm the evidence includes a request or trace identifier, route or provider, a time window, and deployment or dependency context where relevant.
   In the browser, confirm the scenario-owned investigation checklist shows four pending checks before the run, active feedback while queued/running, and four completed checks with the finding.
   Expand the tool trace and confirm every query has a purpose, stable name, enabled state, availability, and duration.
6. Page and acknowledge a responder, or send `response_type=timeout` to verify fallback escalation.
7. For a local-remediation scenario, propose, approve, execute, and verify the allowed action; the incident ends as `resolved`. For the external-dependency scenario, confirm the incident ends as `unfixable` without a local action.
8. Read the incident timeline and confirm the workflow events remain ordered.
9. In the UI, confirm the selected incident auto-selects its investigation context, a completed result offers only an explicit deeper-investigation option, responder controls target the newest page, acknowledgement closes ownership, remediation controls explain their evidence before approval, and failures appear in the toast region rather than in the page layout.
10. For a resource snapshot, list the read-only analyzers, submit resources with a namespace or label filter, and confirm the response contains only normalized findings and suggested inspection steps.
11. In the browser, open the `Kubernetes health` tab, click `Run sample scan`, and confirm the panel reports the detected problems, scanned resources, four finding cards, six read-only analyzers, and no cluster changes.
12. For the Helm extension, run `helm lint`, install with `helm upgrade --install`, wait for the API rollout, run `helm test`, and repeat the browser workflow through the chart’s port-forwarded services.
13. Repeat one scenario for a second incident and confirm `Similar past incidents` shows the earlier statement, category, and resolution without changing the deterministic finding.
14. With a configured model gateway, request one allowed and one disallowed extra query; confirm the allowed result is cited only after collection and the disallowed request is recorded without execution.
15. In `Evidence used`, confirm prompt tokens, completion tokens, estimated cost, and the slowest source are shown; verify the persisted result contains source durations and retrieval latency.
16. For a new scenario, validate and trigger it with `./scripts/add-scenario.sh <definition.json>`, open the printed incident ID, and confirm the registered scenario appears in the console.

## Failure-mode checks

| Check | Expected result |
| --- | --- |
| Repeated `source_event_id` | Existing alert returned with `duplicate: true` |
| New scenario registered as data | Scenario listed publicly without its hidden cause; investigation produces its declared finding; registration survives a restart |
| Incomplete or built-in scenario registration | Rejected with a validation error and no state change |
| Wrong scenario for an incident service | `409` and no investigation or action created |
| Slow evidence source | Source is marked degraded/unavailable within its deadline |
| Responder timeout | Primary page escalates once and fallback page is delivered once |
| Repeated action idempotency key | Original action record is returned |
| Stale page/action version | Decision is rejected without changing the newer state |
| Restart during durable work | Worker recovery resumes or safely retries leased work |
| Queue metrics | `GET /api/v1/jobs/metrics` returns bounded counts and timings without job payloads |
| Queue benchmark | `./scripts/benchmark-queue.py --count 20` completes bounded work and reports throughput without changing the default runtime |
| Missing model configuration | Deterministic finding remains available with explicit degraded model status |
| Local model mode | `MODEL_GATEWAY_MODE=local` returns bounded structured enrichment without credentials or action authority |
| Required operator roles | `AUTH_MODE=required` rejects missing or insufficient tokens before protected workflow mutations |
| Request correlation | `X-Request-ID` is returned and `GET /api/v1/metrics` reports bounded route counts and p50/p95 timings |
| Empty or small similar-incident history | `similar_incidents` is unavailable with a clear uncertainty note |
| Similar-incident retrieval failure | Deterministic finding remains unchanged and the retrieval source is degraded |
| Disallowed model evidence query | Request is rejected in telemetry and no unapproved provider call occurs |
| Evidence-loop bound reached | Investigation completes with a recorded stop reason and no raised error |
| Telemetry estimate unavailable | Counts remain bounded and cost remains finite and non-negative |
| Verified local action | Incident transitions to `resolved` and the timeline records verification and resolution |
| External dependency finding | Incident transitions to `unfixable` and no local action is proposed |
| Approved synthetic checkout | Order succeeds and no incident is created |
| Declined synthetic checkout | One `checkout-api` incident is created without payment credentials in its payload |
| Slow checkout journey | One `payments-api` incident is created with a latency-regression alert |
| Delayed fulfillment journey | One `orders-worker` incident is created with a disk-pressure alert |
| Onboarding script | One valid definition is registered and one incident ID is printed |

## Commerce failure walkthrough

1. Open `http://localhost:8003` and add one product.
2. Run `Try slow checkout` and `Try delayed fulfillment` to create the two operational incidents from the store.
3. Run `Open failed checkout`, choose the declined test card, and submit the payment through the store backend on port `8004`.
4. In a separate operator-console tab, locate each incident and confirm its investigation context is auto-selected.
5. Run the investigations, notify and acknowledge the owners, and verify the captured messages in `http://localhost:8002` contain the finding and suggested next step.

No local remediation is offered for this scenario. The console preserves the incident as an external-dependency case for human follow-up.

## Repeatable demo

```bash
./scripts/reset-demo.sh
./scripts/demo.sh
./scripts/verify-commerce-demo.sh
```

The scripts cover all three scenarios, duplicate/late/flapping/out-of-order delivery, the degraded service-health path, and the complete store-payment-to-responder-inbox path. They are safe to repeat against the local Compose stack.

Run `./scripts/verify-submission.sh` after starting Compose for the final combined local proof.

## Verification record

The current local verification includes the Docker/PostgreSQL backend suite, frontend smoke tests and production build, liveness/readiness checks, live scenario delivery, persisted workflow checks, the demo-store journeys on ports `8003` and `8004`, and frontend HTTP serving on port `8000`. Hosted deployment is outside this local assignment boundary.

The frontend interaction pass also includes a newest-page regression test, server-detail error handling, toast dismissal/timeout behavior, primary-action hierarchy, removal of decorative step labels, a single responder section, and structured model-readout rendering.

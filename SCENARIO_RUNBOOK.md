# Scenario Runbook

## Scenario matrix

| Scenario | Service | Expected finding | Safe next step |
| --- | --- | --- | --- |
| `deployment_regression` | `payments-api` | Latency regression after a version change | `rollback` |
| `disk_pressure` | `orders-worker` | Disk usage is high and cleanup is degraded | `clear_disk` |
| `third_party_outage` | `checkout-api` | Dependency failures with degraded health evidence | `failover` |

## Tester workflow

1. Start Compose and confirm `/api/v1/readiness` returns `{"status":"ready","database":"ok"}`.
2. Select one scenario with `POST /api/v1/simulator/scenarios`.
3. Generate deliveries with `POST /api/v1/simulator/alerts`.
4. Confirm duplicate deliveries do not create duplicate incidents or timeline events.
5. Investigate the matching incident and check evidence, finding, confidence, uncertainty, citations, and model status.
   For the e-commerce proof, confirm the evidence includes a request or trace identifier, route or provider, a time window, and deployment or dependency context where relevant.
6. Page and acknowledge a responder, or send `response_type=timeout` to verify fallback escalation.
7. For a local-remediation scenario, propose, approve, execute, and verify the allowed action; the incident ends as `resolved`. For the external-dependency scenario, confirm the incident ends as `unfixable` without a local action.
8. Read the incident timeline and confirm the workflow events remain ordered.
9. In the UI, confirm the selected incident keeps its own scenario, responder controls target the newest page, queued investigations disable duplicate starts, and failures appear in the toast region rather than in the page layout.

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
| Missing model configuration | Deterministic finding remains available with explicit degraded model status |
| Verified local action | Incident transitions to `resolved` and the timeline records verification and resolution |
| External dependency finding | Incident transitions to `unfixable` and no local action is proposed |
| Approved synthetic checkout | Order succeeds and no incident is created |
| Declined synthetic checkout | One `checkout-api` incident is created without payment credentials in its payload |

## Commerce failure walkthrough

1. Open `http://localhost:8003`, add one product, and proceed to checkout.
2. Select the declined test card and submit the payment through the store backend on port `8004`.
3. In a separate operator-console tab, locate the new `checkout-api` incident and confirm it selected the third-party-outage scenario.
4. Run the investigation and confirm the finding cites dependency and service-health evidence.
5. Page the owner and verify the captured message in `http://localhost:8002` contains the finding and suggested next step.

No local remediation is offered for this scenario. The console preserves the incident as an external-dependency case for human follow-up.

## Repeatable demo

```bash
./scripts/reset-demo.sh
./scripts/demo.sh
./scripts/verify-commerce-demo.sh
```

The scripts cover all three scenarios, duplicate/late/flapping/out-of-order delivery, the degraded service-health path, and the complete store-payment-to-responder-inbox path. They are safe to repeat against the local Compose stack.

## Verification record

The current local verification includes the Docker/PostgreSQL backend suite, frontend smoke tests and production build, liveness/readiness checks, live scenario delivery, persisted workflow checks, and frontend HTTP serving on port `8000`. Hosted deployment is outside this local assignment boundary.

The frontend interaction pass also includes a newest-page regression test, server-detail error handling, toast dismissal/timeout behavior, primary-action hierarchy, removal of decorative step labels, a single responder section, and structured model-readout rendering.

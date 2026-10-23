# Documentation Status

## Current feature parity audit

| Version | Scope | Current result |
|---|---|---|
| 0.0 | Baseline, simulator, and runtime | Implemented; static checks and live readiness pass |
| 0.1 | Simulator controls and typed actions | Implemented; deterministic behavior covered by the backend suite |
| 0.2 | Alert normalization, deduplication, correlation, and timeline | Implemented; live duplicate delivery returned `duplicate: true` |
| 0.3 | Durable incident state and recovery guards | Implemented; PostgreSQL persistence and version checks are present |
| 0.4 | Evidence-first investigation and model boundary | Implemented with durable investigation jobs; fresh worker-backed live investigation completed with model analysis |
| 0.5 | Paging, replies, ownership, and escalation | Implemented; rebuilt Docker/PostgreSQL suite passed with the worker running |
| 0.6 | Approval, durable execution, attempts, and verification | Implemented; rebuilt Docker/PostgreSQL suite passed with migrations `002_jobs.sql` and `003_action_attempts.sql` |
| 0.7 | Incident UI and selection safety | Implemented; frontend smoke tests, build, and port `8000` health pass |
| 0.8 | Resilience, security, and cost bounds | Implemented; Docker/PostgreSQL backend suite returned 37 passing tests with no warnings |
| 0.9 | Tests and deterministic evaluation | Implemented; golden cases cover all three scenarios and the Docker suite returned 39 passing tests with no warnings |
| 1.0 | Compose, documentation, and demo delivery | Implemented; clean-checkout defaults, runnable demo/reset scripts, and live-change coverage are present |
| parity | Cross-document and executable-contract closure | Complete for the local assignment boundary; evidence provenance, page context, prompt contract, schema/API catalog, UI context, static checks, frontend build, graph refresh, and Docker/Postgres verification are aligned. Reference parity add-ons are documented separately and not implemented |

The approved HLD and LLD remain the authority for boundaries and relationships. The current implementation includes durable investigation and action jobs, action-attempt, verification, delivery-attempt, and worker-startup pieces required by those documents.

## Baseline runtime

Status: Implemented and verified locally through the Docker/Postgres stack.

Implemented:

- FastAPI service with liveness and PostgreSQL readiness endpoints.
- React + TypeScript frontend shell.
- Python worker process.
- PostgreSQL service in Docker Compose.
- Frontend on host port `8000`.
- Backend on host port `8001`.
- Three deterministic simulator scenarios.
- Simulator evidence query, alert, typed action, reset, and verification endpoints.
- Alert webhook normalization, fingerprinting, deduplication, incident correlation, and timeline read APIs.
- PostgreSQL-backed incident, alert, and timeline persistence with versioned backend migrations applied at startup.
- Transactional alert idempotency and restart-safe incident reads.
- Validated incident state transitions with timeline events and version checks.
- Bounded deterministic investigation with evidence identifiers, findings, confidence, uncertainty, and citations.
- PostgreSQL-backed investigation, evidence, and finding records.
- Visible degraded results when an evidence source is unavailable.
- Model boundary with sensitive-value masking, structured response validation, and safe degraded statuses.
- Contradictory evidence detection and versioned investigation caching.
- Optional file-backed simulator state for local restart recovery.
- Simulator delivery ordering/delay controls and action idempotency keys.
- Restart-safe reuse of persisted investigations.
- Structured-output adapter configuration for a Responses-compatible provider.
- Persisted primary/fallback pages with acknowledgement, reply, and one-time escalation.
- Typed action proposals, human approval/rejection, idempotent execution, verification, and timeline audit events.
- Scenario and target validation before an action can be approved.
- Stable incident selection while the UI refreshes its list.
- Serialized timeline sequence allocation for concurrent workflow writes.
- Stale-response protection for rapid incident selection changes.
- Active-page and scenario/target-matched action selection in the UI instead of first-item assumptions.
- Frontend selection smoke tests and reproducible locked Docker installs.
- Investigation control and evidence review surface with findings, confidence, uncertainty, citations, source availability, timestamps, and masked payloads.
- Investigation lifecycle transition and timeline recording for received incidents.
- Backend scenario/service and investigation-state checks before action proposals.
- React incident list and timeline view with refresh and empty/error states.
- Explicit simulator responder/dependency failure controls.
- Service/time-window incident correlation beyond explicit correlation keys.
- Startup recovery for interrupted actions and overdue pages.
- Opt-in HTTP boundaries for model-backed investigation, notification delivery, service ownership lookup, and unknown-action reconciliation.
- Compose loads database and runtime credentials from `.env`; secret values are not written into `docker-compose.yml`.
- Backend and frontend use multi-stage production images; the backend runs non-root, and the frontend serves the built application through an unprivileged web server with API proxying.
- Durable jobs now persist queued, leased, succeeded, retried, and dead-lettered work with idempotency keys and lease timestamps.
- The worker claims typed action jobs, executes them through the workflow boundary, and recovers overdue pages during polling.
- Page delivery attempts are persisted, including fallback delivery records.
- Action attempts and post-action verifications are persisted separately from the action proposal.
- Worker startup waits for API migration readiness and retries transient database-startup failures.
- Feature 8 bounds evidence collection with concurrent per-source deadlines, caps model evidence and prompt size, applies configurable model and external-boundary deadlines, version-stamps investigation cache keys, and delays durable retries with capped exponential backoff.
- Feature 9 adds committed golden investigation cases with expected categories, safe next steps, confidence bounds, citation checks, required evidence sources, and prompt-version alignment.
- Feature 10 adds clean-checkout Compose defaults, repeatable all-scenario demo/reset scripts, and a focused live-change analyzer path.
- The UI refreshes the selected incident while polling, supports free-form page replies, and displays queued and running action states.

## Environment-dependent verification:

- The model gateway now applies its documented default URL when only a credential is configured. Persisted non-completed investigations retry when the provider is configured; the running container must be recreated after changing `.env` so it receives the current credential. The worker has dedicated egress for configured external model calls.
- External notification, ownership, and action-executor calls are environment-configured. Their real HTTP adapter paths are verified against a local HTTP boundary with bearer headers, bounded payloads, response validation, and fallback behavior. Hosted deployment verification is intentionally out of scope for this local test assignment.
- Provider URL and response format are read from `MODEL_GATEWAY_URL` and `MODEL_GATEWAY_FORMAT`; the worker-backed live provider path is verified with the configured environment.

## Verification record:

- `docker compose up -d --build` previously started the Compose services with healthy Postgres.
- `curl http://localhost:8001/api/v1/readiness` returned `{"status":"ready","database":"ok"}`.
- The latest rebuilt Docker/PostgreSQL run returned `35 passed in 19.81s` with no warnings; this includes the localhost HTTP boundary integration test. The API and worker containers remained healthy after startup.
- `npm test` returned 3 passing frontend selection checks, and `npm run build` passed.
- The evidence review change passed the same frontend build, backend test, Docker/Postgres readiness, and frontend HTTP checks.
- Live Feature 5–7 happy path persisted an acknowledged page, a verified action, and seven timeline events.
- Live timeout retry path persisted one escalated primary page and one delivered fallback page without duplication.
- Frontend health check on port `8000` returned HTTP 200.
- Boundary adapter tests cover opt-in configuration, bearer-token forwarding, response validation, and local fallback.
- The external-boundary integration test exercised real localhost HTTP requests for ownership lookup, notification delivery, and action reconciliation, including bearer headers and exact bounded payloads.
- Dependency-aware incident correlation and stale human-decision version guards are covered in the current implementation and test suite.
- Live host verification accepted the exact application-generated Responses payload with HTTP 200, and the response parser produced all required structured fields. A fresh worker-backed investigation after the egress fix completed with `model_status=completed`, model analysis present, one finding, and four evidence groups.
- The restart recovery audit found and fixed overdue-page row handling before the final handoff.
- The current parity pass adds migration `003_action_attempts.sql`; the migration and separate attempt/verification records are covered by the rebuilt Docker/PostgreSQL suite.
- A fresh live investigation request returned a queued response, and the worker completed it against PostgreSQL with persisted model analysis, one finding, and four evidence groups after the worker environment and egress wiring were corrected.
- The latest rebuilt Docker/PostgreSQL run returned `37 passed in 20.00s` with no warnings, including slow-evidence degradation and configurable external-boundary timeout coverage.
- The Feature 9 Docker/PostgreSQL run returned `39 passed` with no warnings; the frontend smoke suite remains at 3 passing tests and the frontend build passes.
- Feature 10 verification includes Compose config validation, the full Docker backend suite, frontend tests/build, and documentation checks. The demo scripts are ready for local runtime execution after `docker compose up --build`.
- The parity closure verification added page context to delivery, refreshed the code graph, passed the restricted-reference scan, and completed the frontend build plus a 40-test Docker/Postgres suite.

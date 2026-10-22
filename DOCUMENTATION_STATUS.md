# Documentation Status

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
- PostgreSQL-backed incident, alert, and timeline persistence with startup schema initialization.
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

Environment-dependent verification:

- The model gateway now applies its documented default URL when only a credential is configured. Persisted non-completed investigations retry when the provider is configured; the running container must be recreated after changing `.env` so it receives the current credential.
- External notification, ownership, and action-executor live calls remain environment-dependent until their URLs are configured; their adapters and contract tests are present.

Verification record:

- `docker compose up -d --build` started all seven services with healthy Postgres.
- `curl http://localhost:8001/api/v1/readiness` returned `{"status":"ready","database":"ok"}`.
- `docker compose run --rm api pytest -q tests` returned `31 passed, 1 warning` after the version-guard and migration changes.
- `npm test` returned 3 passing frontend selection checks, and `npm run build` passed.
- The evidence review change passed the same frontend build, backend test, Docker/Postgres readiness, and frontend HTTP checks.
- Live Feature 5–7 happy path persisted an acknowledged page, a verified action, and seven timeline events.
- Live timeout retry path persisted one escalated primary page and one delivered fallback page without duplication.
- Frontend health check on port `8000` returned HTTP 200.
- Boundary adapter tests cover opt-in configuration, bearer-token forwarding, response validation, and local fallback.
- Dependency-aware incident correlation and stale human-decision version guards are covered in the current implementation and test suite.
- Live provider verification reached the provider and returned HTTP 403 for the requested model while the authenticated model-list check returned HTTP 200; model access remains an environment configuration item. After fixing the PostgreSQL timeline row-shape mismatch found during the fresh investigation, the rebuilt Docker/Postgres suite returned 31 passing tests.
- The restart recovery audit found and fixed overdue-page row handling before the final handoff.

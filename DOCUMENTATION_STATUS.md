# Documentation Status

## Baseline runtime

Status: Implemented locally; container runtime verification remains open.

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
- React incident list and timeline view with refresh and empty/error states.
- Explicit simulator responder/dependency failure controls.
- Service/time-window incident correlation beyond explicit correlation keys.
- Startup recovery for interrupted actions and overdue pages.

Open:

- Restart recovery for in-progress actions and pages.
- Live configured model response verification with a real credential.
- Full responder and third-party outage orchestration.
- Runtime verification after the latest local container build.
- Full end-to-end scenario tests.

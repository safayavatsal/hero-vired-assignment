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

Open:

- Paging, human response, approval, and action workflow implementation.
- Restart recovery for in-progress investigations and actions.
- Configured model analysis and model failure handling.
- Durable simulator state and full failure orchestration.
- Runtime verification after the local container socket is available.
- Full API, UI, restart-recovery, and end-to-end scenario tests.

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

Open:

- Incident workflow implementation.
- Alert-to-incident persistence and correlation.
- PostgreSQL-backed alert and incident persistence.
- Durable incident state transitions and restart recovery.
- Durable simulator state and full failure orchestration.
- Runtime verification after the local container socket is available.
- Feature tests beyond the baseline health test.

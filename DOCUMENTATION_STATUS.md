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

Open:

- Incident workflow implementation.
- Alert-to-incident persistence and correlation.
- Durable simulator state and full failure orchestration.
- Runtime verification after the local container socket is available.
- Feature tests beyond the baseline health test.

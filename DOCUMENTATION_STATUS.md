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

Open:

- Incident workflow implementation.
- Simulator scenarios and operational actions.
- Runtime verification after the local container socket is available.
- Feature tests beyond the baseline health test.

# Main App Layout

## Goal

Group the primary incident-console frontend, API, worker, migrations, evaluations, and tests under `main-app/` while keeping documentation, scripts, demo applications, and deployment records at the repository root.

## Steps

1. Move tracked backend and frontend files into `main-app/backend/` and `main-app/frontend/`.
2. Update Compose build contexts, local scripts, benchmark imports, source maps, and architecture references.
3. Preserve ports, API paths, runtime commands, test behavior, and demo-store/observability boundaries.
4. Verify old code paths are absent, then run configuration, backend, frontend, demo, and live browser checks.

## Acceptance checks

- `docker compose config -q` passes with the same host ports.
- Compose builds the API, worker, and main frontend from `main-app/`.
- Backend imports and tests work from `main-app/backend/`.
- Main frontend tests/build work from `main-app/frontend/`.
- Scripts and root documentation point to the new code paths; demo folders remain unchanged.
- HLD, LLD, architecture evidence, and pathfinder diagrams identify the new boundaries.
- No API route or durable data location changes.

## Status

Implemented and verified locally; migration is ready for commit.

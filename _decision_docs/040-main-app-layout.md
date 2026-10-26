# Decision Main App Layout

## Decision

Keep repository-level documents, scripts, Compose, demo applications, and deployment records at the root, and group the primary incident product under `main-app/backend/` and `main-app/frontend/`.

## Why

The repository now contains three independently runnable surfaces. A named main-app boundary makes the primary product as easy to locate as the demo surfaces without changing runtime behavior or API ownership.

## Safety

- Compose keeps ports `8000` and `8001`, the existing service names, commands, volumes, and database migrations.
- The move changes filesystem paths only; it does not change API routes, package names, database schema, or persisted data.
- Documentation and generated architecture evidence are updated together so source links remain reviewable.
- Demo store and demo observability remain separate applications.

## Consequences

Local commands that addressed `backend/` or `frontend/` directly now use `main-app/backend/` or `main-app/frontend/`. The layout is clearer, but external scripts that hard-code the old paths need the same path update. The root remains the operational entry point.

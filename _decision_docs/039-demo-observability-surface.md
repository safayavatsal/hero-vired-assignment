# Decision Demo Observability Surface

## Decision

Add a separate local monitoring demo with one backend and one frontend. The backend reads the existing incident and action read models, maps the three built-in services to bounded synthetic signals, and exposes read-only dashboard snapshots. The frontend presents service-specific pages, before/current values, action status, and links back to the incident console.

## Why

This demonstrates monitoring feasibility and remediation impact without adding a second source of truth, a new database, or an external telemetry dependency to the local setup.

## Safety

- Monitoring pages never mutate incidents, actions, or simulator state.
- Incident state remains authoritative in the existing API.
- Synthetic values are labeled as local demo data and are not presented as production measurements.
- The monitoring backend uses bounded internal HTTP reads and degrades with a visible error when the incident API is unavailable.

## Consequences

Compose gains two small services on host ports `8005` and `8006`. Additional demo pages can be added as data profiles without changing the incident workflow. Hosted metrics ingestion, long-term retention, and alert evaluation remain outside this demo boundary.

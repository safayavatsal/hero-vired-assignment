# Demo Observability Surface

## Goal

Give each incident a clickable, read-only monitoring page that makes service health and before/after changes easy to review.

## Steps

1. Add a separate `demo-observability` frontend and backend with no new runtime dependency.
2. Derive three service-specific dashboard pages from the existing incident and action read models.
3. Link verified remediation to the matching monitoring page and provide a backlink to the incident.
4. Add Compose health checks, focused tests, browser verification, and architecture records.

## Acceptance checks

- The on-call assistant has no demo-store header shortcut.
- A verified incident links to a monitoring page on port `8005`.
- The monitoring backend on port `8006` exposes dashboard catalog, health, and incident snapshot endpoints.
- Dashboard pages show service metrics, before/current values, outcome labels, action status, and a direct incident link.
- Resolved actions show improved values; external-dependency incidents remain blocked rather than claiming a fix.
- Compose, backend tests, frontend tests, frontend builds, and browser deep links pass locally.

## Status

Implemented and verified through focused tests, production builds, Compose checks, live API checks, and browser navigation.

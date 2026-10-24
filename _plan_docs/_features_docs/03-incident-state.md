# Plan Incident State

## Goal

Make incident progress durable, explicit, and recoverable.

## Steps

1. Define incident, alert, evidence, finding, page, decision, action, verification, and timeline records.
2. Define states for received, investigating, awaiting human, escalated, action pending, action running, action unknown, resolved, unfixable, and failed.
3. Define legal state transitions and reject invalid transitions.
4. Append an immutable timeline event for every transition and external response.
5. Add startup recovery for investigations and actions left in progress.
6. Assign idempotency keys to webhook deliveries, investigations, pages, and action attempts.
7. Add optimistic concurrency or version checks for human decisions and state updates.

## Acceptance checks

## Implementation status

Implemented:

- PostgreSQL tables for incidents, alerts, and immutable timeline events.
- Repository boundary and startup schema initialization.
- Transactional alert acceptance with source-event idempotency.
- Restart-safe incident, alert, and timeline reads.
- Durable incident version increments and firing/resolved lifecycle updates.
- Deterministic timeline ordering by source time, received time, and sequence.
- Validated incident state transitions with optional optimistic version checks.
- Transition events appended to the incident timeline.
- Investigation results are reused after service restart when the persisted scenario matches.
- Simulator action requests can be made idempotent with a caller-supplied key.
- Startup recovery marks interrupted actions as unknown and escalates overdue pages once.
- Investigation of a received incident transitions it to `investigating` and records an `investigation_started` timeline event.
- Completed investigations record an `investigation_completed` event; findings that have no local remediation transition the incident to `unfixable` and record `incident_unfixable`.
- A verified simulator result transitions the incident to `resolved` and records `incident_resolved`.
- Action proposals require an investigating/awaiting-human incident and a scenario matching the incident service.
- Page responses and action decisions accept an optional incident version token and reject stale decisions.

Boundary verification:

- External notification delivery and ownership resolution are implemented as opt-in adapters.
- Automatic reconciliation of unknown actions is implemented through the action-executor adapter.
- Explicit version tokens on human decisions are implemented and persisted with pages and action proposals.

## Acceptance checks

- Replaying the same alert request does not duplicate alert or timeline records.
- Incident reads come from PostgreSQL after process restart.
- Timeline order is deterministic.
- Invalid state transitions are rejected and valid transitions create timeline events.
- Full external-provider reconciliation remains outside the deterministic local boundary and is covered by opt-in adapter contracts.

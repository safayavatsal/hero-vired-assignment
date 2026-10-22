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

Open:

- Recovery of in-progress investigations and actions.
- Idempotency for investigations, pages, decisions, and action attempts.
- Optimistic concurrency enforcement for human decisions and action updates.

## Acceptance checks

- Replaying the same alert request does not duplicate alert or timeline records.
- Incident reads come from PostgreSQL after process restart.
- Timeline order is deterministic.
- Invalid state transitions are rejected and valid transitions create timeline events.
- Full workflow transition and action-safety checks remain open for later slices.

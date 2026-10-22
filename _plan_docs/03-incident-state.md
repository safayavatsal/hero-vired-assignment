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

- Restarting midway preserves state and resumes safely.
- Replaying the same request does not duplicate side effects.
- An action cannot run after rejection, expiry, or incident closure.
- Timeline order is deterministic.

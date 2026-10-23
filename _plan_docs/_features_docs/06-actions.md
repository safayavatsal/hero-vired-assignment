# Plan Actions And Audit

## Goal

Execute safe, approved simulator actions exactly once and verify their outcomes.

## Steps

1. Define typed requests for restart, rollback, scale, and disk cleanup.
2. Generate action proposals from investigation findings without executing them.
3. Validate target, parameters, allowed action type, incident state, and approval expiry.
4. Bind approval to the exact action parameters and store the approving human.
5. Acquire an idempotency key before execution.
6. Execute through the simulator action boundary, never through model-generated shell text.
7. Record start, progress, completion, failure, timeout, and unknown outcomes.
8. Verify post-action service state before marking success.
9. Reconcile unknown actions before allowing retry.
10. Append every action decision and result to the audit timeline.

## Acceptance checks

- Repeated execution requests run only once.
- Changed parameters require new approval.
- A timeout after completion is detected by verification.
- Rejected, expired, or unapproved actions never execute.

## Implementation status

Implemented:

- Typed action proposals with parameter validation.
- Scenario and target validation before approval.
- Durable approval and rejection records with approving responder.
- Idempotency-key protected simulator execution.
- Post-action verification and timeline audit events.
- Workflow timeline writes serialize sequence allocation under concurrent requests.
- Action proposals are blocked until investigation is in an allowed state and the selected scenario matches the incident service.
- Approved execution is persisted as a durable action job with an idempotency key; the worker claims it under a lease and records completion or failure.
- Each execution creates a separate durable action-attempt record, and verification creates a record linked to that attempt.

Verified locally through Docker/Postgres on 2026-10-22: proposal, approval, simulator execution, and verification persisted as one action with the expected result and timeline events.

Current verification note: the rebuilt Docker/PostgreSQL run passed 34 backend tests with migrations `002_jobs.sql` and `003_action_attempts.sql`; the worker-backed investigation path was also exercised live after the rebuild.

Implemented:

- Unknown actions can be reconciled through `POST /api/v1/actions/{action_id}/reconcile` when an action-executor URL is configured.
- Executor status is validated and persisted with an `action_reconciled` timeline event.
- Missing executor configuration leaves the action unknown and returns an explicit error instead of retrying it.

Boundary verification:

- Configured action-executor reconciliation is covered by adapter contract tests; live verification requires a reachable executor URL.

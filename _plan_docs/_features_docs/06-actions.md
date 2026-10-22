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

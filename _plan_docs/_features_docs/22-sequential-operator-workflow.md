# Sequential Operator Workflow

## Goal

Make the browser workflow unambiguous after a finding is produced: show the result, let the operator request a deeper pass explicitly, close ownership after acknowledgement, and explain the safe action before approval.

## Steps

1. Remove the normal rerun control from the completed investigation state.
2. Add an explicit deeper-investigation request that uses a distinct queued run mode and remains idempotent.
3. Let the operator notify a specific owner email or claim ownership locally, then close the notification step after ownership is accepted.
4. Gate remediation on acknowledgement and show the evidence-backed reason for the recommendation before proposal or approval.
5. Deliver notifications to the resolved owner when available and include incident identity, finding context, evidence, and local navigation links.
6. Make remediation review read-only until the operator chooses Approve and queue or Reject; show execution before/after state until verification.
7. Add an opt-in server-side role boundary so viewer, responder, approver, and administrator permissions are enforced by the API.

## Acceptance checks

- A completed finding remains visible without a normal `Re-run investigation` button.
- `Request deeper investigation` starts a distinct background investigation and does not reuse the completed standard result.
- Acknowledgement is the ownership boundary; the remediation step does not open before it.
- The public scenario listing does not expose a precomputed category or recommended action.
- A local ownership claim creates an acknowledged page without sending a notification.
- The remediation view explains the finding, current condition, and cited evidence before a human approves the action.
- Local notification delivery identifies the specific responder and includes the incident console and responder inbox links.
- Reviewing a remediation produces a sandbox projection without changing simulator state or creating an action decision.
- Approve and Reject are the only controls that create the audited action decision after the projection is visible.
- Approve automatically queues the approved action and the execution before/after state remains visible through verification.
- With `AUTH_MODE=required`, missing or insufficient operator credentials are rejected before workflow mutation.

## Status

Implemented in the backend workflow, local notification boundary, incident console, and focused tests.

# Human-Owned Remediation Flow

## Goal

Make the browser workflow reflect the actual order of operations: evidence produces the category and action, ownership is explicit, approval queues once, and verification keeps the observed before/after state visible.

## Steps

1. Keep scenario analyzer rules internal to the simulator listing; expose the category and recommended action only after investigation completes.
2. Allow the operator to notify a validated owner email or claim ownership locally without sending a notification.
3. Combine approval and queueing in the browser path while retaining the existing additive execute API for compatibility.
4. Persist the selected notification recipient and show execution before/after state until verification completes.
5. Keep the sandbox preview stable during polling, then let the operator verify and explicitly close the incident.
6. Update the HLD, LLD, API, runbook, and browser tests around the new state transitions.

## Acceptance checks

- The public scenario listing does not predeclare the finding category or recommended action.
- A completed investigation provides the category and only then unlocks a matching typed action.
- Owner notification accepts a validated email; local ownership creates an acknowledged page without delivery.
- Approve creates and queues the action without a second Queue control.
- Execution before/after state remains visible through verification, and successful verification reports a verified action without closing the incident.
- The operator receives a direct incident link and explicitly closes the incident after reviewing verification evidence.

## Status

Implemented and verified through focused tests, the complete Docker/PostgreSQL backend suite, frontend tests/build, and live browser/API checks.

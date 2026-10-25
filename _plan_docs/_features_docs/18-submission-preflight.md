# Plan Submission Preflight

## Goal

Make the final local assignment proof repeatable from one command.

## Acceptance checks

- Compose configuration validates.
- Backend readiness and demo-store health respond successfully.
- The incident console and demo store serve HTML successfully.
- The demo-store frontend proxy reaches the demo-store backend successfully.
- The main Docker backend suite and the demo-store backend suite pass.
- The main frontend and demo-store frontend build successfully.
- The commerce verifier proves approved checkout, declined checkout, all three customer-facing scenario handoffs, incident creation, investigation, paging, and captured notification.
- The working tree passes `git diff --check`.

## Status

Implemented in `scripts/verify-submission.sh`, the Docker health check, and the local Kubernetes readiness probe.

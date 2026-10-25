# Plan Submission Preflight

## Goal

Make the final local assignment proof repeatable from one command.

## Acceptance checks

- Compose configuration validates.
- Backend readiness and demo-store health respond successfully.
- The incident console and demo store serve HTML successfully.
- The Docker backend suite passes.
- The main frontend and demo-store frontend build successfully.
- The commerce verifier proves approved checkout, declined checkout, incident creation, investigation, paging, and captured notification.
- The working tree passes `git diff --check`.

## Status

Implemented in `scripts/verify-submission.sh`.

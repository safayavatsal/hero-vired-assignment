# 023 — Submission Preflight

## Decision

Provide one local verification command that checks the assignment's runnable boundary before submission.

The command validates Compose configuration, PostgreSQL readiness, both served frontends, backend tests, both production frontend builds, the commerce-to-incident workflow, and whitespace errors in the working tree.

## Consequences

- A reviewer can reproduce the most important local proof with one command after starting Compose.
- The check remains local and does not claim hosted deployment or external-provider availability.
- The command intentionally fails on the first broken boundary so the failing stage is visible.

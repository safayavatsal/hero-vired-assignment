# 023 — Submission Preflight

## Decision

Provide one local verification command that checks the assignment's runnable boundary before submission.

The command validates Compose configuration, PostgreSQL readiness, both served frontends, the demo-store frontend proxy, both backend test suites, both production frontend builds, the commerce-to-incident workflow, and whitespace errors in the working tree.

## Consequences

- A reviewer can reproduce the most important local proof with one command after starting Compose.
- The check remains local and does not claim hosted deployment or external-provider availability.
- A storefront container is not ready until its proxied backend health route responds, reducing false-positive deployment checks.
- The command intentionally fails on the first broken boundary so the failing stage is visible.

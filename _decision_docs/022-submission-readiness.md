# 022 — Submission And On-Site Readiness

## Decision

Treat the assignment artifacts as part of the product: the repository must explain its choices, prove the high-risk behavior, and support the four on-site activities through runnable local workflows.

| Requirement | Evidence |
| --- | --- |
| Demonstrate the incident workflow | `DEMO_GUIDE.md`, `SCENARIO_RUNBOOK.md`, and the repeatable commerce verifier |
| Add a scenario live | Runtime scenario registration, persisted definitions, and the public scenario listing |
| Make a live code change | Golden evaluation coverage and the small data-driven scenario extension path |
| Explain scale and safety | `DECISIONS.md`, typed actions, approval gates, verification, leases, and recovery |

## Consequences

- `DECISIONS.md` stays short enough for reviewer orientation while detailed records remain in `_decision_docs/`.
- The local boundary is explicit: hosted credentials, authentication, multi-tenancy, and production deployment are future architecture work, not hidden claims.
- Structured model output is rejected when its fields or citations are malformed; deterministic findings remain the safe fallback.

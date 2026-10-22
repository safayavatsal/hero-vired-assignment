# Human Action Safety

Status: Proposed

## Decision

All mutating actions use typed action requests and require human approval. The backend validates the action type, target, parameters, incident, expiration, and current state before execution.

The LLM may recommend an action but cannot create executable shell commands or bypass policy. An approved action is bound to the exact parameters approved by the human.

## Consequences

- Restart, rollback, scale, and disk-clear actions are auditable.
- Changed actions require fresh approval.
- Autonomous remediation is excluded from the baseline.

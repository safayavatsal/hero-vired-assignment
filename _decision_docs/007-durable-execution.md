# Durable Execution

Status: Proposed

## Decision

Persist incidents, evidence, human decisions, action requests, action attempts, verification results, and timeline events. Use idempotency keys for webhook processing and action execution.

Action outcomes include success, failure, timed out, and unknown. An unknown action is verified before any retry is considered.

## Consequences

- Restarting the process does not lose work.
- An action that completed before a timeout is not repeated blindly.
- The timeline can explain what the system believed and what actually happened.

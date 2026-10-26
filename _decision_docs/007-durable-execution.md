# Durable Execution

Status: Implemented

## Decision

Persist incidents, evidence, human decisions, action requests, action attempts, verification results, and timeline events. Use idempotency keys for webhook processing and action execution. Keep the PostgreSQL-backed queue as the local default, and expose bounded queue metrics before considering a separate broker.

Action outcomes include success, failure, timed out, and unknown. An unknown action is verified before any retry is considered.

## Consequences

- Restarting the process does not lose work.
- An action that completed before a timeout is not repeated blindly.
- The timeline can explain what the system believed and what actually happened.
- Queue wait, lease, retry, completion, and dead-letter behavior can be evaluated from persisted state without exposing job payloads.
- A future broker can implement the same enqueue/claim/complete/fail contract without changing incident or workflow semantics.

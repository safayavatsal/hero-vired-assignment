# System Boundaries

Status: Proposed

## Decision

Separate the system into alert intake, incident lifecycle, simulator, investigation, paging, action execution, audit, and UI boundaries.

The backend owns state transitions, permissions, retries, idempotency, and audit events. The frontend presents state and submits human decisions. The simulator provides controlled production-like behavior.

## Consequences

- The LLM cannot directly mutate state or execute infrastructure actions.
- Each boundary can be tested independently.
- Technology-specific choices remain open for later discussion.

# Incident UI And Timeline

Status: Proposed

## Decision

Provide an incident list and an incident detail view. The detail view renders an ordered timeline containing alerts, correlation, evidence, findings, tool outcomes, pages, human responses, approvals, actions, verification, failures, and resolution.

The backend remains authoritative for state and permissions; the UI does not infer completed actions from optimistic state.

## Consequences

- Operators can understand the complete incident story.
- Refreshing the page does not lose or duplicate events.
- The UI directly demonstrates assignment coverage.

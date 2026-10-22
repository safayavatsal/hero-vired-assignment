# Paging And Escalation

Status: Proposed

## Decision

Page a primary responder with incident context, evidence summary, suggested next step, and available decisions. Track sent, delivered, acknowledged, replied, approved, rejected, expired, and escalated states.

If the responder does not acknowledge within the scenario timeout, escalate to the configured fallback responder and record the transition.

## Consequences

- Human waiting time is distinct from investigation time.
- A page is actionable rather than a generic notification.
- No-response behavior is deterministic in demos and tests.

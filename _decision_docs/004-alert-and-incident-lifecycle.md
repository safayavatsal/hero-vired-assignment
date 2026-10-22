# Alert And Incident Lifecycle

Status: Proposed

## Decision

Normalize every webhook into a canonical alert event with a stable fingerprint, source timestamp, received timestamp, lifecycle state, and correlation attributes.

Use durable incident states for investigation, human response, action execution, uncertainty, resolution, and unfixable outcomes. Repeated, late, out-of-order, and flapping alerts update the same incident when their fingerprints and correlation rules indicate the same cause.

## Consequences

- Duplicate webhooks do not create duplicate incidents.
- Event arrival order is not treated as event time order.
- Correlation behavior is explainable and testable.

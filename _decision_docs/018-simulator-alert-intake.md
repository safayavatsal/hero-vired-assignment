# Simulator Alert Intake

## Decision

Route simulator-generated deliveries through the same alert intake path used by external webhooks. Keep the simulator responsible for deterministic delivery behavior, while the API boundary owns normalization, deduplication, correlation, persistence, and timeline creation.

## Why

The assignment requires alerts to behave like webhooks and the demo must create trackable incidents from a clean start. Returning deliveries without accepting them left the demo dependent on a separate hand-written request and did not exercise the complete product flow.

## Lifecycle rule

Duplicate copies of one lifecycle share a source event identity. A firing event and a later resolved event receive different identities and source timestamps. PostgreSQL derives the incident lifecycle from the newest source event so an older out-of-order delivery cannot overwrite newer state.

## Consequences

- The simulator remains deterministic and does not gain direct persistence responsibilities.
- The alert pipeline is exercised by both simulated and external-shaped deliveries.
- The demo response contains generated deliveries and their accepted incident results.
- Hosted alert-provider integration remains outside this local assignment boundary.

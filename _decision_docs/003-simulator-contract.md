# Simulator Contract

Status: Proposed

## Decision

Build a deterministic simulator with explicit services for alerts, logs, metrics, deployments, responders, actions, delays, outages, and scenario reset.

Each scenario owns its initial state, hidden cause, generated signals, available evidence, expected diagnosis, and permitted actions.

## Consequences

- Scenarios are repeatable in demos and tests.
- Failure modes can be triggered without real infrastructure.
- The simulator remains small enough to extend during the on-site session.

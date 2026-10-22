# Plan Simulator

## Goal

Provide repeatable production-like data and behavior without real infrastructure.

## Steps

1. Define simulated services, responders, deployments, logs, metrics, alerts, actions, delays, and outage controls.
2. Add scenario reset and seed operations so every run starts from known state.
3. Implement alert generation with source timestamps and configurable delivery delay, duplication, reordering, and flapping.
4. Implement read-only query tools for logs, metrics, deployment history, service health, and current scenario state.
5. Implement typed simulated actions for restart, rollback, scale, and disk cleanup.
6. Record requested, started, completed, failed, timed-out, and verified action states.
7. Add three scenarios with hidden causes, expected evidence, expected diagnosis, and safe next action.
8. Add controls for slow APIs, unavailable APIs, third-party outage, non-responsive responders, and post-completion action timeout.

## Acceptance checks

- Each scenario can be reset and triggered on demand.
- Each required evidence source is queryable.
- Each action changes simulator state and creates audit data.
- Failure controls are deterministic in tests.

## Implementation status

Implemented in the baseline simulator slice:

- Three deterministic scenarios with hidden causes that are exposed only through evidence queries.
- Scenario selection, reset, state inspection, and alert generation endpoints.
- Duplicate, late, and flapping alert generation controls.
- Logs, metrics, deploy history, and service-health evidence queries.
- Typed action execution with action records and verification.
- Deterministic timeout-after-completion behavior for the rollback scenario.
- Optional file-backed simulator state for restart-safe local runs.
- Explicit delayed and out-of-order delivery controls.
- Action idempotency keys prevent a repeated request from running twice.
- Explicit responder availability and third-party dependency controls are exposed in simulator state.

The external notification and ownership workflow is covered by Feature 5; this simulator supplies its deterministic responder and dependency controls.

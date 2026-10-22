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

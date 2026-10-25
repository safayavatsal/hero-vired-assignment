# Plan Scenario Extensibility

## Goal

Make adding a new incident scenario a data-only change so a new scenario can be registered and investigated during a live session without touching the investigation pipeline or the UI.

## Steps

1. Move each scenario's finding rule (metric, category, statement, confidence, suggested next step, cited sources, uncertainty) into its `ScenarioDefinition`.
2. Replace the hardcoded analyzer chain in the investigation service with a rule-driven matcher; keep a small generic rule registry for reusable metric shapes.
3. Accept an optional scenario definition on `POST /api/v1/simulator/scenarios` so a scenario is registered and selected through the documented "add or select" contract.
4. Persist registered scenarios in simulator state so they survive restarts; forbid replacing built-in scenarios; reject incomplete definitions.
5. Derive the UI scenario list, service mapping, and action types from `GET /api/v1/simulator/scenarios` instead of hardcoded frontend maps.

## Acceptance checks

- A scenario registered as data produces a correct, cited finding end to end.
- Registered scenarios survive a simulator restart and are offered to the UI without their hidden causes.
- Built-in scenarios cannot be replaced and incomplete definitions are rejected.
- All existing golden evaluation cases pass unchanged against the rule-driven matcher.
- A selected incident resolves to its matching scenario even when the public scenario list loads after incident details.

## Status

Implemented. Finding rules now live in scenario definitions, investigation matches rules generically, scenario registration is available through the existing simulator scenario endpoint, and the frontend derives scenario metadata from the API. The console also corrects its selected scenario when scenario metadata arrives after incident details. Backend suite (55 tests), frontend tests (6 tests), and the production frontend build pass.

# Decision Architecture Documentation Refresh

## Decision

Keep the Pathfinder packet as a dated navigation and handoff artifact, while treating feature plans, HLD, LLD, decision records, source code, and tests as the current authority. Regenerate the rendered architecture map from the checked-in architecture JSON whenever the runtime boundaries change.

## Why

The repository now has a primary application plus two independent demos and several bounded investigation capabilities. A single source-backed architecture map and an updated navigation packet reduce stale-path ambiguity without adding runtime dependencies or changing application behavior.

## Scope of the current map

- Main application frontend, API, worker, PostgreSQL state, retrieval, model, notification, and runtime boundaries.
- Demo store and its alert handoff.
- Demo observability UI/API and read-only incident/action snapshot boundary.
- Fixed evidence fan-out, similar-history retrieval, optional allowlisted evidence requests, and persisted telemetry.
- Scenario onboarding, human-owned remediation, verification, and explicit closure.

## Consequences

The architecture JSON and generated HTML must be updated together. The Pathfinder packet can preserve historical reasoning and handoff context, but it must not be treated as an executable specification. Browser visual approval remains a separate check from deterministic architecture validation.

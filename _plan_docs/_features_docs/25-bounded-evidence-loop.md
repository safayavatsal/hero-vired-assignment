# Plan Bounded Evidence Loop

## Goal

Allow configured model analysis to request a small amount of additional read-only evidence without weakening the fixed investigation boundary.

## Implementation

- Keep the four-source fan-out and deterministic finding as the baseline.
- Accept optional model evidence requests, then validate source, query, and parameters against a server-side allowlist.
- Permit similar-history retrieval and per-source re-query only.
- Bound rounds, additional requests, evidence items, and wall-clock time through environment settings.
- Record rejected requests and the stop reason in model telemetry; never raise because a bound was reached.

## Acceptance checks

- Disallowed queries are rejected without execution.
- A valid re-query is appended as evidence and the next model response must cite only collected identifiers.
- Round, request, item, and wall-clock limits end the loop safely.
- No configured model performs no additional loop work.

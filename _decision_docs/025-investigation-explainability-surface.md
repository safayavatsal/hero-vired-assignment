# Decision Investigation Explainability Surface

## Decision

The investigation view will lead with a short structured brief and expose provenance progressively:

| Surface | Default view | Expanded view |
| --- | --- | --- |
| Finding | Cause, confidence, next step, and citations | Uncertainty details |
| Model analysis | Current condition, likely cause, next step, provider status, and latency | Model-specific citations and provider note |
| Evidence | Source availability and query timing | Parameters and raw payload |
| Audit | Human-readable event summaries | Display-safe event payloads |

## Why

The operator needs a fast decision surface first and implementation evidence second. Showing every JSON payload immediately makes the workflow harder to follow during an incident review. Progressive disclosure preserves auditability while keeping the primary path readable.

## Consequences

- The browser now makes tool provenance and model telemetry visible without changing the API contract.
- Raw evidence remains available for reviewers who need it.
- The UI does not invent a narrative when the model is unavailable; the deterministic finding and degraded status remain separate.

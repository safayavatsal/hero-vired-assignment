# Evidence First Investigation

Status: Proposed

## Decision

The investigation collects structured evidence first, then asks the LLM to summarize and rank hypotheses. Every conclusion must reference evidence identifiers.

Investigation output must contain the current condition, likely cause, confidence, suggested next step, cited evidence, and explicit uncertainty when evidence is missing or contradictory.

## Consequences

- The model explains facts instead of inventing observations.
- Missing or unavailable sources remain visible.
- Prompt evaluation can check evidence coverage and unsupported claims.

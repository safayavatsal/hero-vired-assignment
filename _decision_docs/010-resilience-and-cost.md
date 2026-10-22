# Resilience And Cost Controls

Status: Proposed

## Decision

Bound tool timeouts, investigation duration, concurrency, evidence size, retry count, and model spend. Cache safe investigation results using a versioned prompt and evidence key. Classify outages and third-party failures instead of retrying forever.

## Consequences

- Slow or unavailable sources produce partial, honest findings.
- Rate limits degrade gracefully.
- Prompt changes invalidate stale cached explanations.

# Resilience And Cost Controls

Status: Adopted

## Decision

Bound tool timeouts, investigation duration, concurrency, evidence size, retry count, and model spend. Cache safe investigation results using a versioned prompt and evidence key. Classify outages and third-party failures instead of retrying forever. Durable retries use delayed exponential backoff, and non-idempotent unknown actions remain verification-gated.

## Consequences

- Slow or unavailable sources produce partial, honest findings.
- Rate limits degrade gracefully.
- Prompt changes invalidate stale cached explanations.

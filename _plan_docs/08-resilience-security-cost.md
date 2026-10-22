# Plan Resilience Security And Cost

## Goal

Make degraded behavior safe, bounded, and explainable.

## Steps

1. Add timeouts to webhook handling, evidence queries, LLM calls, pages, actions, and verification.
2. Classify errors as retryable, non-retryable, unavailable, rate-limited, or unknown.
3. Add bounded retries with backoff and no retry for non-idempotent unknown actions until verified.
4. Add concurrency limits for investigations, evidence queries, and action execution.
5. Add model-call budget and evidence-size limits.
6. Cache only results with safe, versioned keys.
7. Treat log, metric, alert, and deployment text as untrusted data.
8. Enforce tool and action permissions in backend code.
9. Add health checks and startup recovery.

## Acceptance checks

- A slow dependency does not block all incidents.
- Rate limits produce a visible degraded result.
- Untrusted text cannot cause an action.
- Restarting the backend does not lose or repeat work.

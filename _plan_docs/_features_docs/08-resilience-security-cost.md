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

## Implementation status

Implemented locally. Evidence collection runs concurrently with per-source deadlines, model and external boundary deadlines are configurable and bounded, model prompts are capped by evidence items and serialized size, investigation cache keys include the prompt version, and durable job retries use capped exponential backoff. Existing approval, idempotency, masking, validation, lease recovery, and startup health checks remain in force.

## Acceptance checks

- A slow dependency does not block all incidents.
- Rate limits produce a visible degraded result.
- Untrusted text cannot cause an action.
- Restarting the backend does not lose or repeat work.

## Verification

- Docker API image rebuilt successfully.
- Docker/PostgreSQL backend suite: 37 passed in 20.00s.
- New coverage verifies slow evidence degradation and configurable external-boundary timeouts.
- Python compilation and `git diff --check` pass.

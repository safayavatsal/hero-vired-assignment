# Feature Baseline

Status: Required baseline

This document is the scope contract for the assignment. Add-on features are excluded until every item below is implemented and verified.

## Product workflow

1. Receive alert webhooks.
2. Normalize, deduplicate, order, and correlate alerts.
3. Create or update a durable incident.
4. Investigate using simulated logs, metrics, deployment history, and an LLM.
5. Produce a short summary covering the current problem, likely cause, suggested next step, and cited evidence.
6. Page the correct human with an actionable message.
7. Handle acknowledgement, reply, approval, rejection, timeout, and escalation.
8. Execute only approved, typed infrastructure actions.
9. Verify the result and record the complete audit timeline.
10. Display incidents and their timelines in the React interface.

## Simulator

- Generate alerts on demand.
- Expose logs, metrics, and deployment history.
- Support at least three scenarios with hidden root causes.
- Support restart, rollback, scale, and disk-clear actions.
- Simulate slow, unavailable, delayed, duplicate, and out-of-order responses.
- Simulate action timeouts after the action has completed.
- Simulate responders who do not answer.
- Simulate an unfixable third-party outage.
- Keep an audit record of what actually ran.

## Reliability and safety

- Deduplicate repeated webhooks.
- Handle late, out-of-order, and flapping alerts.
- Correlate multiple symptoms into one incident.
- Persist state across process restarts.
- Prevent duplicate actions with idempotency keys.
- Represent uncertain action outcomes explicitly.
- Retry only safe and retryable operations.
- Treat logs and external text as untrusted data.
- Enforce action allowlists outside the LLM.
- Bound investigation time, concurrency, and model spend.
- Handle unavailable tools, rate limits, and partial evidence.

## Required delivery

- `docker compose up` starts the system.
- `README.md` explains setup, scenarios, and a short tour.
- `DECISIONS.md` summarizes major choices, alternatives, weaknesses, and scale considerations.
- `AI_USAGE.md` records AI use, one caught mistake, and deliberately authored work.
- Tests cover the highest-risk behavior.
- Git history remains available for review.

## On-site readiness

- Demonstrate all three scenarios.
- Add a new scenario during the live session.
- Make small live code changes.
- Explain scale, bottlenecks, prompt quality, and production safety.

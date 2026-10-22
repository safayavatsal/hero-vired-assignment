# Plan Investigation

## Goal

Produce a concise, honest, evidence-backed investigation.

## Steps

1. Build an investigation context from the incident, correlated alerts, scenario state, and recent deployments.
2. Run deterministic analyzers for latency, disk pressure, deployment regression, dependency outage, and alert correlation.
3. Query simulated logs, metrics, and deploys through bounded tools.
4. Store each tool query, parameters, result, duration, failure, and evidence identifier.
5. Remove or mask sensitive values before sending text to the LLM.
6. Use a structured prompt requiring current condition, likely cause, confidence, suggested next step, citations, and uncertainty.
7. Validate the model response schema and reject unsupported evidence identifiers.
8. Handle missing data, contradictory findings, LLM errors, timeouts, and rate limits without fabricating a conclusion.
9. Cache safe results using incident evidence and prompt version; invalidate on changed evidence or prompt.

## Acceptance checks

- Every finding cites stored evidence.
- Unavailable sources are visible in the result.
- A third-party outage is classified as unfixable.
- Malicious log text cannot change tool permissions or action policy.

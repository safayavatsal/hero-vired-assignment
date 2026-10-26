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

## Implementation status

Implemented in the current slice:

- Bounded collection of logs, metrics, deployment history, and service health.
- Stable evidence identifiers for collected source results.
- Persisted provenance for each source query, parameters, collection time, duration, and failure.
- Deterministic analyzers for deployment regression, disk pressure, and dependency outage.
- Structured findings with confidence, uncertainty, suggested next step, and evidence citations.
- Investigation and evidence read APIs.
- PostgreSQL persistence for investigations, evidence, and findings.
- Visible degraded findings when an evidence source is unavailable.
- Sensitive-value masking before model use.
- Structured model gateway with timeout, rate-limit, unavailable, and invalid-response handling.
- Evidence-citation validation for model responses.
- Explicit model status for unavailable and degraded model analysis.
- Contradictory metric detection and versioned in-process investigation caching.
- Environment-configured structured-output adapter for a Responses-compatible model provider.
- Received incidents are advanced to `investigating` with a durable `investigation_started` timeline event.
- Scenario/service mismatches are rejected before evidence is accepted for an incident.
- Prompt contract changes are tracked by a stable contract hash alongside the prompt version.
- The three scenarios now expose concrete e-commerce signals such as payment routes, trace IDs, queue state, deployment commits, provider names, and time windows.
- Evidence collection uses a small named tool registry, and each result carries a bounded tool trace with availability and duration metadata.
- Investigation persistence records safe model telemetry without credentials or raw provider responses; the UI displays structured model analysis separately from deterministic findings.
- Similar completed findings are stored with deterministic vectors and retrieved through a fifth bounded evidence source; retrieval context is additive and the deterministic finding is calculated before it.
- Configured model analysis may request only allowlisted read-only re-queries through a bounded loop; every returned item re-enters evidence and citation validation.

Boundary verification:

- The configured model adapter is ready for a live credential; deterministic fallback, response validation, and retry behavior are covered locally.
- Investigation requests now enqueue durable jobs and return a queued status; the worker performs evidence collection and persists the completed result. The gateway sends the exact Responses-compatible payload with the configured model and parses structured output. A fresh worker-backed live investigation completed with model analysis, one finding, and four evidence groups. The latest rebuilt Docker/PostgreSQL verification returned 35 passing backend tests with no warnings.

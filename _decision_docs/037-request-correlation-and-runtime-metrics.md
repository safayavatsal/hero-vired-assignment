# Decision 037: Request correlation and runtime metrics

## Decision

Generate or accept a bounded `X-Request-ID` at each HTTP boundary, return it to the caller, propagate it to configured outbound boundaries, and expose dependency-free in-process HTTP metrics at `GET /api/v1/metrics`.

Metrics use fixed route templates and status classes. They retain a bounded latency sample per route and report request count, error count, p50, p95, and maximum duration.

## Safety and limits

- Raw URLs, query strings, credentials, payloads, and request identifiers are not metric labels.
- Runtime metrics reset on process restart and are operational evidence, not a durable billing or SLO store.
- Structured request logs contain the request ID, route template, status class, and duration only.
- The demo store propagates its request ID when it emits an alert to the API.

## Consequences

- A request can be followed through the API and configured outbound boundaries.
- Local operators can inspect endpoint latency and errors without another service.
- Durable cross-process tracing and long-term metric retention remain future deployment concerns.

# Plan Cost And Latency Telemetry

## Goal

Make model and evidence cost/latency visible without exposing provider credentials or raw responses.

## Implementation

- Estimate prompt and completion tokens from bounded JSON payloads when provider usage is absent.
- Persist a finite non-negative estimated cost with the existing model telemetry.
- Persist per-source duration, availability, and similar-history retrieval latency.
- Show prompt tokens, completion tokens, estimated cost, and slowest source in the evidence panel.

## Acceptance checks

- Telemetry is present after configured and unconfigured investigations.
- Estimated cost is finite and non-negative.
- Source timing remains available for degraded and successful evidence.
- No secret or raw provider response is persisted.

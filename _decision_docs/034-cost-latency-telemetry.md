# Decision 034: Cost and latency telemetry

## Decision

Keep telemetry in the existing investigation record. Estimate tokens from the bounded serialized prompt and structured response, calculate cost from optional local rate settings, and persist source-level timing beside availability.

## Safety and limits

- Missing provider usage data never blocks an investigation.
- Cost defaults to zero when no local rate is configured; it is always finite and non-negative.
- Telemetry contains counts, durations, statuses, and bounded source names only.
- Credentials and raw provider responses remain excluded.

## Consequences

- The operator can identify prompt/completion size and the slowest source from the evidence panel.
- Cost figures are estimates, not billing records.
- Existing persisted investigations remain readable because the telemetry fields are additive JSON values.

# Plan Alert Pipeline

## Goal

Turn unreliable alert webhooks into canonical events and incidents.

## Steps

1. Validate the webhook envelope and preserve the raw payload for audit.
2. Normalize source, service, severity, labels, timestamps, lifecycle, and description.
3. Compute a stable event fingerprint from source identity and meaningful alert fields.
4. Reject or acknowledge duplicate deliveries without creating duplicate side effects.
5. Store source time separately from receive time and order timeline rendering by event time with deterministic tie-breaking.
6. Detect resolution, repetition, and flapping without losing the raw events.
7. Correlate alerts by service, dependency, time window, and shared scenario identifiers.
8. Create or update the owning incident and append a timeline event for every delivery.

## Acceptance checks

- Duplicate, late, and out-of-order webhooks are handled correctly.
- Repeated alerts do not create a new incident each time.
- Correlated alerts appear under one incident with explainable grouping.
- Raw and normalized alert data remain available.

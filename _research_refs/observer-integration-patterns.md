# Embedded Observer Integration Patterns

## Findings

- An observed service should identify itself with a stable logical service name and can include deployment context so evidence remains attributable across instances. [Service resource conventions](https://opentelemetry.io/docs/specs/semconv/resource/service/)
- Failure telemetry should capture the failed operation and a bounded failure classification. Error status is contextual: an expected, handled provider failure should be recorded without turning customer-facing recovery into an internal diagnostic surface. [Recording errors](https://opentelemetry.io/docs/specs/semconv/general/recording-errors/)
- Correlation identifiers make logs, traces, and events from one checkout attempt usable together. [Log correlation](https://opentelemetry.io/docs/specs/otel/logs/)
- Attribute sets should remain small and bounded; potentially sensitive or unbounded values should not become indexed attributes. [Semantic-convention guidance](https://opentelemetry.io/docs/specs/semconv/how-to-write-conventions/)

## Minimal pattern for this project

1. The observed service contains a small observer client rather than customer-facing operator links.
2. Checkout code calls that client only after the simulated payment provider reports an unavailable authorization dependency.
3. The client emits a bounded event with service, operation, failure category, attempt correlation, product identifiers, order total, and timestamp.
4. Cardholder, card number, expiry, and security code remain outside the observer payload.
5. Failure to deliver an observation must not change the customer-facing payment outcome; it remains a failed payment with a customer-safe reference.

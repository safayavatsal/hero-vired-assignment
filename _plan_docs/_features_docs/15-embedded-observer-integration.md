# Plan Embedded Observer Integration

## Goal

Make the demo store behave like a customer-facing application observed by a separate operational product.

## Steps

1. Move checkout-failure event construction into a dedicated observer client in the store backend.
2. Emit only bounded operational metadata after a simulated authorization dependency becomes unavailable.
3. Keep customer payment results independent from observer-delivery status.
4. Remove internal operator links and incident identifiers from the store UI.
5. Preserve the smoke verifier's ability to validate the full operator path.

## Acceptance checks

- An approved payment creates no event.
- A provider-unavailable payment returns a customer-safe failed result and emits one canonical event when the observer is available.
- Payment credentials never appear in the observer event.
- Observer-delivery failure does not turn the customer result into a monitoring error.
- The customer UI contains no links to the operator console or responder inbox.
- Separate explicitly correlated checkout attempts remain separate incidents during the repeatable demo run.

## Status

Implemented. The store backend owns the small observer client, the customer UI shows only a payment reference, and the observer-delivery-degradation case is covered by a focused backend test. Explicit correlation keys prevent distinct checkout attempts from joining through broad service-time correlation. Static compilation, the store production build, Compose validation, and the project restricted-reference scan pass. The running-stack smoke verifier remains the proof for the cross-service path.

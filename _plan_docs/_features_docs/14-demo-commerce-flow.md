# Plan Demo Commerce Flow

## Goal

Demonstrate a realistic local journey from product selection through a controlled payment failure, incident investigation, responder notification, and audited operator response.

## Steps

1. Add a standalone store frontend with a product catalog, cart, and checkout form on host port `8003`.
2. Add a standalone store backend with catalog and deterministic payment APIs on host port `8004`.
3. Build a minimal failure alert containing only synthetic operational identifiers and send it from the store backend to the canonical alert endpoint.
4. Return a customer-safe payment reference while the operator independently locates the checkout incident in the on-call console.
5. Deliver responder pages to a local captured-email inbox through the existing notification boundary.
6. Verify approved payment, declined payment, alert deduplication, incident creation, investigation, paging, email capture, and browser navigation.
7. Keep a repeatable smoke verifier for the same backend path used by the browser demonstration.

## Acceptance checks

- A presenter can add a product, enter synthetic details, and complete an approved payment without creating an incident.
- A declined payment creates an incident through the normal alert pipeline and returns a customer-safe payment reference.
- Repeating the demonstration creates a fresh incident, while retrying one payment event remains idempotent.
- Payment fields are validated only by the store backend; no card number, security code, customer address, or customer email appears in the alert or incident payload.
- The matching investigation produces cited checkout dependency evidence.
- Paging the responder produces a visible captured email containing the finding and suggested next step.
- The entire local stack starts through Compose and remains demonstrable from the browser.

## Status

Implemented as separate store backend and frontend projects. Eleven store-backend tests cover approved and declined payments, request validation, product validation, all three customer scenario mappings, the privacy-bounded observer contract, endpoint behavior, and observer-delivery degradation. The main backend has 50 sandbox-compatible passing tests, the main frontend has five passing workflow tests, both production frontend builds pass, Compose validates, and the local Kubernetes manifest parses. On 2026-10-25, the Compose smoke verifier completed an approved payment, a declined payment that created a fresh incident, a completed investigation, a delivered responder page, and one captured inbox message. Browser confirmation was also completed for the store-to-console workflow.

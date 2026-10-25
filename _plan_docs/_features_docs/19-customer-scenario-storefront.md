# Plan Customer Scenario Storefront

## Goal

Make all three built-in incident scenarios reproducible from the customer-facing demo store, so a reviewer can create a realistic commerce symptom without posting an operator alert by hand.

## Steps

1. Keep the existing approved and declined checkout paths unchanged.
2. Add a store-side customer scenario endpoint that validates the cart and emits only bounded operational metadata.
3. Add three visible demo journeys: slow checkout after a release, delayed fulfillment from worker disk pressure, and provider-unavailable checkout.
4. Return customer-safe references and plain-language outcomes without exposing the operator console or sensitive payment fields.
5. Extend the commerce verifier and store tests to cover the three scenario paths.

## Acceptance checks

- A customer can start each built-in scenario from `http://localhost:8003`.
- The deployment-regression path creates a `payments-api` latency incident.
- The disk-pressure path creates an `orders-worker` disk incident.
- The provider-outage path still uses the checkout form and creates a `checkout-api` incident.
- Unknown scenarios and unknown products are rejected before an alert is sent.
- The store observer payload contains product and attempt metadata only; it never contains card data.
- The operator continues the investigation, paging, and action workflow in the separate console.

## Status

Implemented in the standalone store backend and frontend. The focused store suite passes 9 tests and the store frontend production build passes. Full Compose verification remains the final runtime check after the images are rebuilt.

# Customer Scenario Storefront

## Decision

| Area | Decision | Reason |
| --- | --- | --- |
| Customer trigger | Add three visible demo journeys to the store homepage. | A reviewer can reproduce the production symptom from a customer action instead of hand-writing an alert. |
| Store boundary | Add one store-owned scenario endpoint and keep the operator console separate. | The customer app reports bounded operational metadata without becoming an internal admin tool. |
| Checkout path | Preserve the declined-card checkout for provider failure. | It demonstrates a real customer payment attempt and keeps the existing privacy contract intact. |
| Other failures | Model release latency and fulfillment-worker disk pressure as customer-safe degraded or delayed outcomes. | Those symptoms are realistic at the storefront boundary while still mapping to the existing incident scenarios. |

## Consequences

- All three built-in scenarios can be started from the demo store.
- The observer sends only scenario, product, attempt, and total metadata; payment credentials remain inside the payment request.
- The store does not gain links to or controls for the operator console.
- The commerce verifier now proves the two direct scenario journeys in addition to approved and declined checkout.

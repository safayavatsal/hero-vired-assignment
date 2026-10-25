# Embedded Observer Integration

Status: Adopted

| Area | Decision | Reason |
| --- | --- | --- |
| Customer experience | Remove operator-console and inbox links from the store. | Customers should see payment outcomes, not internal incident tooling. |
| Integration boundary | Place a small observer client in the store backend. | The monitored application emits its own bounded operational event at the failure boundary. |
| Event contract | Include service, operation, failure category, attempt correlation, product identifiers, total, and timestamp. | Investigation receives useful operational context without collecting payment credentials. |
| Delivery failure | Keep the payment result failed even when event delivery is unavailable. | Monitoring must not decide the customer transaction outcome. |
| Demonstration | Use the returned payment reference for the customer flow and the smoke verifier for operator proof. | The presentation can show both perspectives without coupling the two interfaces. |

## Consequences

- The store becomes a realistic observed application rather than a shortcut into the operator console.
- The incident system continues to receive the canonical alert contract.
- The observer remains intentionally small: no second queue, database, or retry engine is added to the demo store.

# Demo Commerce Integration

Status: Adopted

## Decision

| Area | Decision | Reason |
| --- | --- | --- |
| Storefront | Keep the demo store in `demo-store/frontend` and expose it on host port `8003`. | The customer journey remains visibly separate from the operator console. |
| Store backend | Keep catalog and payment behavior in `demo-store/backend` and expose its API on host port `8004`. | The payment failure crosses a real service boundary before it becomes an incident. |
| Payment | Use explicitly synthetic card inputs and deterministic approved/declined outcomes. | The demo needs repeatability and must never process real payment data. |
| Alerting | Send failed attempts through the canonical alert webhook. | This proves the actual intake, deduplication, correlation, persistence, and timeline path. |
| Investigation | Map failed authorization to the existing checkout dependency scenario. | It reuses the approved evidence and investigation workflow. |
| Notification | Deliver responder pages to a local captured-email inbox. | It demonstrates notification delivery without an external account or hosted provider. |
| Safety | Keep investigation and paging operator-driven and keep actions approval-gated. | The demo must not bypass the product's human-control boundary. |

## Consequences

- The complete demonstration starts from a customer-facing action rather than a hand-written alert payload.
- Synthetic payment details enter only the demo-store backend and are never persisted or sent to the assistant.
- Each payment attempt starts a fresh demo incident, while retrying that exact source event remains idempotent.
- The store does not introduce another database, queue, or incident model.

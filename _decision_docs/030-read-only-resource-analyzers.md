# Decision 030: Read-only resource analyzer surface

## Decision

Add a separate, read-only resource analysis surface beside the existing incident workflow. It uses named analyzers, explicit resource filters, normalized findings, stable evidence, and suggested next steps without changing alerts, investigations, actions, or persistence. The incident console exposes it through a dedicated `Kubernetes health` tab with a local sample scan so the capability is demonstrable from the browser as well as the API.

## Why

- Expands diagnosis from fixed scenarios to common resource health checks.
- Keeps each analyzer independently testable and discoverable.
- Preserves human approval and prevents analysis from mutating cluster state.
- Allows local snapshot-based verification without requiring authentication or a hosted cluster.
- Gives a presenter a visible result without requiring a live cluster.

## Initial coverage

| Analyzer | Resource kinds | Primary checks |
| --- | --- | --- |
| `pod` | `Pod` | Pending/failed phases, container waits, abnormal termination, readiness |
| `deployment` | `Deployment` | Replica mismatch and failed progression |
| `service` | `Service` | Missing selectors and empty endpoint sets |
| `event` | `Event` | Warning events and related-resource context |
| `node` | `Node` | Readiness and pressure conditions |
| `persistent_volume_claim` | `PersistentVolumeClaim` | Unbound storage claims |

## Consequences

- The new API is additive and accepts a sanitized resource snapshot.
- Namespace, kind, name, label, and analyzer filters are explicit.
- The browser sample uses a fixed snapshot and clearly labels the result as read-only.
- Live cluster collection and mutating remediation remain separate follow-up work.

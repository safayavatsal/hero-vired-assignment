# Low-Level Design Overview

This LLD describes the main classes, their responsibilities, method signatures, and connections. It does not contain implementation logic.

## Package boundaries

| Package | Main responsibility |
| --- | --- |
| `domain` | Incident, evidence, decision, action, and timeline concepts |
| `application` | Use-case services coordinating domain operations |
| `ports` | Interfaces for persistence, evidence, paging, model access, and actions |
| `adapters` | PostgreSQL, simulator, paging, model, and HTTP implementations |
| `execution` | Durable jobs, worker handlers, leases, retries, and verification |
| `api` | Request validation, authorization, and response mapping |

## Connection rules

- API handlers call application services.
- Application services depend on ports, not concrete adapters.
- Domain objects do not call databases, HTTP clients, model providers, or simulator clients.
- Worker handlers call the same application services used by API-triggered work.
- Repositories persist domain state and timeline events.
- The runtime sequence in `05-runtime-sequence-flow.md` shows the interaction order.
- The final Mermaid diagram in `06-lld-system-diagram.md` shows all class connections together.

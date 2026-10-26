# Low-Level Design Overview

This LLD describes the main classes, their responsibilities, method signatures, and connections. It does not contain implementation logic.

## Package boundaries

The main application package root is `main-app/backend/app/`; the operator console root is `main-app/frontend/src/`.

| Package | Main responsibility |
| --- | --- |
| `main-app/backend/app/domain` | Incident, evidence, decision, action, and timeline concepts |
| `main-app/backend/app/application` | Use-case services coordinating domain operations |
| `main-app/backend/app/ports` | Interfaces for persistence, evidence, historical retrieval, paging, model access, and actions |
| `main-app/backend/app/adapters` | PostgreSQL, simulator, retrieval, paging, model, and HTTP implementations |
| `main-app/backend/app/execution` | Durable jobs, worker handlers, leases, retries, and verification |
| `main-app/backend/app/api` | Request validation, authorization, and response mapping |
| `demo-store/backend` | Product catalog, synthetic payment validation, deterministic routing, and failure-alert delivery |
| `demo-store/frontend` | Customer-facing catalog, cart, checkout, and incident handoff |

## Connection rules

- API handlers call application services.
- Application services depend on ports, not concrete adapters.
- Domain objects do not call databases, HTTP clients, model providers, or simulator clients.
- Worker handlers call the same application services used by API-triggered work.
- Repositories persist domain state and timeline events.
- Retrieval is a separate port: deterministic embeddings and ranked historical context are injected into the investigation service and persisted through a PostgreSQL adapter.
- The optional model loop can request only named evidence tools; the service executes, bounds, and revalidates every request server-side.
- The runtime sequence in `05-runtime-sequence-flow.md` shows the interaction order.
- The final Mermaid diagram in `06-lld-system-diagram.md` shows all class connections together.
- The store-specific classes and request flow are summarized in `07-demo-store.md`.

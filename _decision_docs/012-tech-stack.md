# Technology Stack

Status: Recorded

## Decision

Use the following technologies because they directly support the system boundaries, durable incident workflow, human approval flow, simulator, and incident timeline.

| Area | Technology | Why we are using it | Why we are not using the alternative |
| --- | --- | --- | --- |
| Backend API | Python with FastAPI | Strong typing, request validation, and a natural fit for investigation workflows | A separate backend language would add unnecessary boundaries to the simulator and model integration |
| Frontend | React with TypeScript and Vite | Matches the required interface and keeps incident views and timeline components easy to change | A larger frontend framework would add structure that the incident UI does not need |
| Persistence | PostgreSQL | Provides transactions, durable state, idempotency, audit records, and timeline ordering | A document database would make state transitions and audit consistency harder to enforce |
| Background work | Python worker backed by PostgreSQL | Supports investigations, actions, retries, leases, and restart recovery | A workflow platform would add operational complexity before the workflow boundaries are proven |
| Model integration | Provider-neutral adapter with validated structured output | Keeps model calls replaceable and prevents model output from directly changing state or executing actions | Direct model calls from handlers would couple business logic to one provider and weaken validation |
| UI data flow | REST with polling | Simple, observable, and sufficient for incident updates and human decisions | WebSockets or streaming add connection-management complexity before it is required |
| Local runtime | Docker Compose | Gives every contributor the same API, worker, frontend, and database environment | Kubernetes would add deployment machinery that is not needed for the local system |
| Verification | Pytest, Vitest, React Testing Library, and Playwright | Covers domain behavior, simulator behavior, UI behavior, and one complete browser flow | A large end-to-end-only suite would be slower and less precise for state-machine failures |

Do not add a separate queue/cache service, a vector database, or an external paging provider unless a measured requirement makes one necessary. PostgreSQL can initially provide the durable job, cache, idempotency, and audit storage needed by the system.

## Consequences

- Backend state transitions, approvals, actions, verification, and audit history remain durable and testable.
- The frontend remains focused on incident lists, incident details, timelines, and human decisions.
- The worker can recover investigations and actions after a restart.
- The model provider can change without changing domain or UI code.
- Docker Compose provides one consistent local environment.

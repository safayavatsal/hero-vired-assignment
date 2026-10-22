# AI Usage

## Deliberately authored work

The project is being developed as peer programming. The project owner directs and approves the design; implementation logic is AI-assisted and reviewed against that design.

## Deliberately authored work

The following work is deliberately authored and reviewed as project design work:

- The high-level design decisions and architecture boundaries.
- The low-level design structure, class responsibilities, methods, variables, and relationships.
- The LLD structure decision and the consolidated decision index.
- The API catalog organization and documentation structure.

- The baseline runtime boundaries and service responsibilities.
- The class-level LLD and the relationships between its classes.

## AI-assisted implementation

The baseline runtime wiring, service configuration, health endpoints, worker process, and frontend shell were implemented with AI assistance from the approved design.

The simulator service, scenario definitions, evidence queries, typed actions, timeout state, verification endpoint, and focused tests were implemented with AI assistance from the approved simulator plan.

The alert normalization, fingerprinting, duplicate handling, incident correlation, timeline ordering, incident read APIs, and focused tests were implemented with AI assistance from the approved alert-pipeline plan.

The PostgreSQL repository, schema initialization, transactional alert persistence, idempotent delivery handling, and restart-safe incident reads were implemented with AI assistance from the approved incident-state plan.

The explicit incident transition validation, optimistic version check, transition endpoint, and transition timeline records were implemented with AI assistance from the approved incident-state plan.

The bounded evidence collection, deterministic scenario analyzers, finding schema, citation validation, investigation API, and focused tests were implemented with AI assistance from the approved investigation plan. Model analysis remains deliberately unconfigured in this slice.

The investigation repository, durable evidence and finding records, restart-boundary test, and unavailable-source handling were implemented with AI assistance from the approved investigation plan.

The model gateway boundary, sensitive-value masking, structured-response validation, citation checks, and safe model failure statuses were implemented with AI assistance from the approved investigation plan. No provider credential is stored in the repository.

The simulator restart state, delivery delay/order controls, action idempotency, correlation-window lookup, restart-safe investigation reuse, and structured-output provider adapter were implemented with AI assistance from the approved Feature 1–4 plans. The project owner remains responsible for the design boundaries and review of these changes.

The durable paging, fallback escalation, typed approval workflow, simulator execution boundary, audit timeline events, and incident timeline UI were implemented with AI assistance from the approved paging, action, and UI plans. The human-authored workflow boundary remains explicit: provider text cannot execute actions, and approval is required before execution.

Implementation-specific mistakes caught and changes directly authored by the project owner will be recorded as the implementation progresses.

# Decisions

This file is the index of the detailed decision records in [`_decision_docs/`](_decision_docs/).

| Decision | Brief |
| --- | --- |
| [001 — Scope Baseline](_decision_docs/001-scope-baseline.md) | Establishes the required baseline before add-on features. |
| [002 — System Boundaries](_decision_docs/002-system-boundaries.md) | Separates alert intake, incidents, simulator, investigation, paging, actions, audit, and UI responsibilities. |
| [003 — Simulator Contract](_decision_docs/003-simulator-contract.md) | Defines deterministic alerts, evidence sources, typed actions, scenarios, and failure controls. |
| [004 — Alert And Incident Lifecycle](_decision_docs/004-alert-and-incident-lifecycle.md) | Defines correlation, deduplication, ordering, flapping, and incident state transitions. |
| [005 — Evidence First Investigation](_decision_docs/005-evidence-first-investigation.md) | Requires evidence-backed findings with citations, uncertainty, and bounded model use. |
| [006 — Human Action Safety](_decision_docs/006-human-action-safety.md) | Requires typed allowlisted actions and explicit human approval before execution. |
| [007 — Durable Execution](_decision_docs/007-durable-execution.md) | Defines durable jobs, leases, retries, idempotency, recovery, and verification. |
| [008 — Paging And Escalation](_decision_docs/008-paging-and-escalation.md) | Defines actionable pages, acknowledgement, timeouts, and escalation. |
| [009 — Incident UI And Timeline](_decision_docs/009-ui-timeline.md) | Defines the incident list, detail view, and ordered event timeline. |
| [010 — Resilience And Cost Controls](_decision_docs/010-resilience-and-cost.md) | Bounds timeouts, evidence, retries, concurrency, caching, and model spend. |
| [011 — Evaluation And Delivery](_decision_docs/011-evaluation-and-delivery.md) | Defines scenario evaluation, prompt regression checks, Compose startup, and required delivery artifacts. |
| [012 — Technology Stack](_decision_docs/012-tech-stack.md) | Records the selected backend, frontend, persistence, worker, model, runtime, and test technologies. |
| [013 — Architecture Documentation](_decision_docs/013-architecture-documentation.md) | Separates system architecture, runtime flow, domain model, and UI documentation. |
| [014 — LLD Structure](_decision_docs/014-lld-structure.md) | Defines the superficial class-level LLD structure and final UML overview. |
| [015 — Parity Closure](_decision_docs/015-parity-closure.md) | Aligns evidence provenance, UI context, evaluation contracts, schema, and API documentation with the executable product. |
| [016 — Reference Parity Boundary](_decision_docs/016-reference-parity-boundary.md) | Records function-level alignment and the six broader capability gaps without changing the assignment boundary. |
| [017 — Assignment Flow Parity Closure](_decision_docs/017-assignment-flow-parity-closure.md) | Defines explicit resolved/unfixable outcomes, usable human follow-up, and the evidence required for assignment-flow closure. |
| [018 — Simulator Alert Intake](_decision_docs/018-simulator-alert-intake.md) | Routes simulator deliveries through canonical alert intake and preserves lifecycle ordering. |
| [019 — Demo Commerce Integration](_decision_docs/019-demo-commerce-integration.md) | Drives the real incident workflow from a synthetic storefront payment failure and local captured email. |

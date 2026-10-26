# Decisions

## Executive summary

| Decision area | Choice | Why | Trade-off |
| --- | --- | --- | --- |
| API and UI | FastAPI backend, React + TypeScript frontend | Matches the assignment and keeps the operator workflow easy to inspect | Two application runtimes must be packaged together |
| Persistence | PostgreSQL owns incidents, evidence, pages, actions, jobs, and timeline events | Restart-safe state and transactional human decisions | Requires migrations and a running database |
| Background work | Small PostgreSQL-backed worker with leases, retries, and idempotency | Durable investigations and actions without introducing a workflow platform | Queue throughput is limited until a broker is added |
| Investigation | Bounded evidence tools plus deterministic findings, with optional structured model enrichment | The product remains useful when the provider is slow, unavailable, or wrong | The baseline supports a small scenario set rather than open-ended diagnosis |
| Remediation | Typed allowlisted actions require explicit human approval and post-action verification | Prevents model text from becoming executable infrastructure commands | No autonomous remediation in the baseline |
| Demo boundary | Local simulator, synthetic commerce app, captured inbox, and Compose | Reproduces production-like behavior without external accounts | It is not a production multi-tenant deployment |

Known weaknesses are the intentionally local provider boundary, synthetic infrastructure, limited resource families, no authentication or multi-tenancy, and a polling UI rather than streamed progress. These are visible in the runbook and are not disguised as production proof.

For one million users, the next architecture step is to separate stateless API and worker pools, move jobs to a managed queue, partition PostgreSQL by tenant and incident time, add read replicas and a search/index layer for evidence, store large raw payloads outside the relational database, enforce tenant-scoped authorization, and apply per-tenant/model budgets with queue-level backpressure. The current boundaries make those changes additive rather than requiring a rewrite.

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
| [020 — Embedded Observer Integration](_decision_docs/020-embedded-observer-integration.md) | Separates customer checkout from bounded operational event reporting. |
| [021 — Scenario Extensibility](_decision_docs/021-scenario-extensibility.md) | Makes new incident scenarios data-only through finding rules, runtime registration, and a UI that follows the scenario listing. |
| [022 — Submission And On-Site Readiness](_decision_docs/022-submission-readiness.md) | Maps the required demo, live-change, and discussion evidence and closes structured-output validation. |
| [023 — Submission Preflight](_decision_docs/023-submission-preflight.md) | Adds one repeatable local command for the final Compose, test, build, demo, and diff checks. |
| [024 — Customer Scenario Storefront](_decision_docs/024-customer-scenario-storefront.md) | Makes all three built-in incident scenarios reproducible from customer-facing store journeys. |
| [025 — Investigation Explainability Surface](_decision_docs/025-investigation-explainability-surface.md) | Shows the structured brief, tool provenance, model telemetry, and progressive evidence detail in the browser. |
| [026 — Guided Investigation Workflow](_decision_docs/026-guided-investigation-workflow.md) | Presents scenario context automatically and explains ownership, approval, and verification in operator language. |
| [027 — Sequential Operator Workflow](_decision_docs/027-sequential-operator-workflow.md) | Separates completed findings, deeper analysis, ownership acknowledgement, action explanation, and owner-specific notification. |
| [028 — Investigation Runbook Catalog](_decision_docs/028-investigation-runbook-catalog.md) | Makes scenario-owned investigation checks visible before, during, and after a run. |
| [029 — Evidence Tool Catalog](_decision_docs/029-evidence-tool-catalog.md) | Gives each bounded evidence query a stable name, purpose, enabled state, and traceable result. |
| [030 — Read-only Resource Analyzers](_decision_docs/030-read-only-resource-analyzers.md) | Adds discoverable, filtered, read-only resource analysis beside the existing incident workflow. |
| [031 — Helm Local Extension](_decision_docs/031-helm-local-extension.md) | Packages the existing local runtime as an additive Helm workflow while preserving Compose and the raw Kubernetes manifest. |
| [032 — Similar Past Incidents](_decision_docs/032-similar-past-incidents.md) | Adds bounded ranked historical context with deterministic vectors, PostgreSQL persistence, masking, and failure isolation. |
| [033 — Bounded Evidence Loop](_decision_docs/033-bounded-evidence-loop.md) | Allows validated, bounded read-only model re-queries while preserving the fixed no-model path. |
| [034 — Cost And Latency Telemetry](_decision_docs/034-cost-latency-telemetry.md) | Persists bounded token/cost estimates and source timing, then shows a compact evidence-panel summary. |

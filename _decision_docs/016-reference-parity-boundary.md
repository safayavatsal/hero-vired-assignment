# Reference Parity Boundary

Status: Adopted

## Decision

Treat the supplied reference repositories as capability references, not as a requirement for one-to-one function copying. Preserve the current assignment contract and record broader capabilities as additive work until they are explicitly approved.

## Function-level comparison

| Capability | Current product | Parity result | Boundary decision |
| --- | --- | --- | --- |
| Alert intake and incident lifecycle | `AlertPipelineService.accept`, normalization, fingerprinting, correlation, deduplication, transitions, and timeline writes | Aligned | Keep as the core intake contract. |
| Evidence-first investigation | `InvestigationService._collect`, `_findings`, `_uncertainty`, masking, citations, bounded concurrency, and persisted provenance | Aligned for the assignment scenarios | Keep the deterministic provider boundary and structured model response. |
| Human-safe remediation | `WorkflowService.propose_action`, `decide_action`, `execute_action`, `verify_action`, and `reconcile_action` | Aligned | Keep typed actions, approval, idempotency, verification, and unknown-state recovery. |
| Tool and analyzer registry | Fixed scenario evidence providers and an allowlisted action set | Partial | A dynamic plugin/tool registry is an add-on, not a replacement for the current contract. |
| Multi-step investigation | One bounded investigation job with deterministic evidence collection and one model analysis | Partial | Iterative tool-calling loops and conversation continuation require a separate plan. |
| Resource analysis breadth | Three simulator scenarios with four evidence sources | Partial | Generic resource-kind analyzers and live cluster discovery are outside the current assignment boundary. |
| Streaming and follow-up interaction | Queued job polling and five-second UI refresh | Partial | Streaming responses, conversation history, and follow-up actions are optional add-ons. |
| Provider and operational integrations | Optional model, ownership, notification, and action-executor HTTP boundaries | Partial | Additional integrations, tracing, cost telemetry, and dynamic provider refresh remain separate work. |
| Test depth | Scenario golden cases, unit tests, localhost boundary tests, and Docker/Postgres verification | Aligned for the assignment | Broader analyzer fixture coverage belongs with any approved add-on. |

## Consequences

- The product is functionally aligned with the approved assignment documents without importing unrelated platform breadth.
- The six partial areas are visible, prioritized, and cannot be mistaken for completed functionality.
- No source code is copied from the supplied references.
- Any add-on must receive its own plan, tests, documentation update, and acceptance decision.

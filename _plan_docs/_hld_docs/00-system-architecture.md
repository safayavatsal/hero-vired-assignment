# System Architecture

This high-level architecture describes the runtime boundaries and the executable PostgreSQL schema used by the product.

The main application code is grouped under `main-app/backend/` and `main-app/frontend/`; documentation and demo applications remain at the repository root.

## 1. Runtime architecture

```mermaid
flowchart LR
    Shopper[Demo shopper] --> Storefront[Demo store frontend]
    Storefront -->|catalog and payment API| StoreAPI[Demo store backend]
    StoreAPI -->|failed payment alert| API
    Responder[On-call engineer] --> UI[Main app frontend]
    Responder --> MonitorUI[Demo observability frontend]
    UI -->|REST and polling| API[Main app backend API]
    MonitorUI -->|read-only dashboard requests| MonitorAPI[Demo observability backend]
    MonitorAPI -->|bounded incident/action reads| API
    Operator[Configured operator token] -.->|role authorization| API
    API --> Metrics[Bounded runtime metrics]
    API --> Store[(PostgreSQL system of record)]
    API --> Jobs[(PostgreSQL durable jobs)]
    Worker[Main app worker] --> Jobs
    Worker --> Store
    Worker --> Simulator[Production simulator]
    Worker --> Retrieval[Historical finding retriever]
    Retrieval --> Store
    Worker --> Model[Provider-neutral model adapter]
    Model -.->|validated bounded evidence requests| Worker
    Worker --> Pager[Paging and executor boundaries]
    API --> Inbox[Local captured responder inbox]
```

## 2. Responsibility boundaries

| Component | Owns | Does not own |
| --- | --- | --- |
| Main app frontend | Incident list, detail, timeline, evidence review, and human decision forms | State transitions, action execution, inferred completion, or payment processing |
| Demo observability frontend | Service dashboard pages, before/current comparisons, and incident backlinks | Incident state, action execution, or durable metric storage |
| Demo store frontend | Product selection, cart, synthetic checkout form, and payment result | Incident creation, payment processing, or durable state |
| Demo store backend | Product catalog, synthetic payment validation, deterministic outcome, and bounded failure alert | Real payments, card persistence, or incident investigation |
| FastAPI API | Validation, idempotency, state transitions, read models, and audit events | Long-running investigation or direct model execution |
| Python worker | Investigation jobs, action execution, verification, retries, leases, and overdue-page recovery | Browser presentation or unvalidated human intent |
| PostgreSQL | Incidents, alerts, evidence, findings, pages, actions, jobs, attempts, verifications, and timeline history | External alert generation or model reasoning |
| Historical finding retriever | Deterministic finding vectors, bounded ranked history lookup, and retrieval timing | Deterministic diagnosis, model authorization, or incident state |
| Production simulator | Deterministic alerts, evidence sources, typed actions, and failure controls | Production credentials or arbitrary command execution |
| Model and delivery boundaries | Structured analysis, bounded allowlisted evidence requests, telemetry, optional delivery, ownership, local captured email, and reconciliation | Direct authorization or incident truth |
| Operator role boundary | Optional server-side viewer, responder, approver, and administrator permissions for mutations | Full identity lifecycle, tenancy, or session management |
| Runtime metrics | Request IDs, structured request records, and bounded route latency summaries | Durable tracing backend or long-term metric retention |
| Demo observability backend | Read-only service profiles and bounded incident/action snapshots for local monitoring pages | Incident mutation, metric retention, or production telemetry ingestion |

## 3. Relational schema catalog

All identifiers are UUIDs unless stated otherwise. JSON fields contain validated data and never executable instructions.

| Table | Fields and constraints |
| --- | --- |
| `incidents` | `id` PK, `fingerprint` UNIQUE NOT NULL, `service`, `severity`, `status`, `summary` NOT NULL, `version` NOT NULL, `created_at`, `updated_at` |
| `alerts` | `id` PK, `incident_id` FK, `source_event_id` UNIQUE NOT NULL, `fingerprint`, `source`, `service`, `severity`, `alert_type`, `labels` JSONB, `description`, `lifecycle`, `source_time`, `received_time`, `raw_payload` JSONB |
| `investigations` | `id` PK, `incident_id` FK UNIQUE, `scenario_id`, `generated_at`, `model_status`, `model_error`, `model_analysis` JSONB, `prompt_version`, `tool_trace` JSONB, `model_telemetry` JSONB |
| `investigation_evidence` | `(investigation_id, id)` PK/FK, `source_type`, `query`, `parameters` JSONB, `availability`, `observed_at`, `collected_at`, `duration_ms`, `error`, `items` JSONB |
| `investigation_findings` | `(investigation_id, id)` PK/FK, `category`, `statement`, `confidence`, `suggested_next_step`, `evidence_ids` JSONB, `uncertainty` |
| `finding_embeddings` | `id` PK, `incident_id`, `investigation_id`, `service`, `category`, `statement`, `suggested_next_step`, deterministic `embedding` JSONB, `created_at`; indexed by creation time |
| `pages` | `id` PK, `incident_id` FK, `(incident_id, level)` UNIQUE, `responder`, `fallback_responder`, `status`, `deadline_at`, `response_type`, `response_text`, `incident_version`, `created_at`, `updated_at` |
| `action_proposals` | `id` PK, `incident_id` FK, `scenario_id`, `action_type`, `target`, `parameters` JSONB, `status`, `approval_expires_at`, `approved_by`, `idempotency_key` UNIQUE, `simulator_action_id`, `result` JSONB, `incident_version`, `created_at`, `updated_at` |
| `action_attempts` | `id` PK, `action_proposal_id` FK, `(action_proposal_id, attempt_number)` UNIQUE, `status`, `simulator_action_id`, `result` JSONB, `started_at`, `completed_at` |
| `verifications` | `id` PK, `action_attempt_id` FK, `status`, `observed_state` JSONB, `verified_at` |
| `jobs` | `id` PK, `incident_id` FK nullable, `job_type`, `status`, `payload` JSONB, `idempotency_key` UNIQUE, `attempts`, `max_attempts`, `available_at`, `lease_until`, `leased_at`, `completed_at`, `last_error`, `created_at`, `updated_at` |
| `page_delivery_attempts` | `id` PK, `page_id` FK, `(page_id, attempt_number)` UNIQUE, `status`, `external_id`, `created_at` |
| `timeline_events` | `id` PK, `incident_id` FK, `event_type`, `event_time`, `received_time`, `(incident_id, sequence_number)` UNIQUE, `payload` JSONB |

## 4. Integrity rules

- Every alert has a source idempotency key and preserved validated payload.
- Every evidence item retains its query, parameters, result, availability, timing, and failure state.
- Historical context is indexed only after a completed finding and is returned as evidence; unavailable, empty, or slow retrieval adds uncertainty without changing the deterministic finding.
- Additional model evidence requests are allowlisted, citation-validated, and bounded by rounds, items, requests, and wall-clock time.
- Investigation telemetry records source durations, retrieval latency, bounded token estimates, and finite cost estimates without raw provider responses.
- Every action is typed, linked to an incident, and blocked until explicit approval exists.
- Every action attempt has an outcome and a separate verification record; a timeout never implies success.
- Every durable job has a lease, retry count, and idempotency key.
- Queue state exposes bounded counts and wait/processing timings without returning job payloads.
- Every user-visible state change emits an incident-local timeline event.
- Validated model output cannot execute an action or mutate incident state directly.

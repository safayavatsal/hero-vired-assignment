# Investigation and Evidence Classes

## Classes

| Class | Responsibility | Main methods |
| --- | --- | --- |
| `InvestigationService` | Coordinate fixed evidence, historical context, bounded model re-queries, finding creation, and telemetry | `investigate()`, `collect_evidence()`, `_query_similar_incidents()`, `_model_analysis()`, `_model_telemetry()` |
| `EvidenceTool` | Name and describe one bounded evidence query | `query(provider)` |
| `EvidenceProvider` | Interface for read-only evidence collection and scenario context | `select_scenario(scenario_id)`, `query_evidence(source_type)`, `finding_rules(scenario_id)` |
| `SimulatorEvidenceProvider` | Implement `EvidenceProvider` through the simulator | `query_evidence()`, `finding_rules()` |
| `ModelGateway` | Interface for structured model analysis | `analyze()` |
| `ProviderModelGateway` | Adapt a configured model provider to `ModelGateway` | `analyze()` |
| `RetrievalRepository` | Index completed findings and return ranked historical context | `index()`, `count()`, `search()` |
| `InMemoryRetrievalRepository` | Deterministic test repository for finding vectors | `index()`, `count()`, `search()` |
| `PostgresRetrievalRepository` | Persist and rank finding vectors in PostgreSQL | `index()`, `count()`, `search()` |
| `InvestigationRepository` | Persist validated findings, evidence, tool trace, agent-loop telemetry, and source timing | `save()`, `get()` |
| `InvestigationHandler` | Execute an investigation job through the application service | `handle(job)` |

## Connections

`InvestigationHandler` calls `InvestigationService`. `InvestigationService` depends on `EvidenceProvider`, `ModelGateway`, `InvestigationRepository`, `RetrievalRepository`, and incident/timeline services. The fixed sources and historical retriever are collected with bounded timeouts. Deterministic findings are created before the historical query; model output may request only allowlisted re-queries, which are collected server-side and passed through citation validation again. The no-model path stops after the fixed evidence flow. Concrete providers are injected at composition time.

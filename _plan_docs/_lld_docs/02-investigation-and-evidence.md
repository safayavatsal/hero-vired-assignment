# Investigation and Evidence Classes

## Classes

| Class | Responsibility | Main methods |
| --- | --- | --- |
| `InvestigationService` | Coordinate evidence collection and finding creation | `investigate()`, `collect_evidence()`, `create_findings()` |
| `EvidenceProvider` | Interface for read-only evidence collection | `collect_logs()`, `collect_metrics()`, `collect_deploys()` |
| `SimulatorEvidenceProvider` | Implement `EvidenceProvider` through the simulator | `collect_logs()`, `collect_metrics()`, `collect_deploys()` |
| `ModelGateway` | Interface for structured model analysis | `analyze_evidence()` |
| `ProviderModelGateway` | Adapt a configured model provider to `ModelGateway` | `analyze_evidence()` |
| `FindingRepository` | Persist validated findings and model-run references | `save_all()`, `list_for_incident()` |
| `InvestigationHandler` | Execute an investigation job through the application service | `handle(job)` |

## Connections

`InvestigationHandler` calls `InvestigationService`. `InvestigationService` depends on `EvidenceProvider`, `ModelGateway`, `FindingRepository`, and `TimelineRepository`. Concrete providers are injected at composition time.

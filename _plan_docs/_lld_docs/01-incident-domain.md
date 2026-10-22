# Incident Domain Classes

## Classes

| Class | Responsibility | Main methods |
| --- | --- | --- |
| `Incident` | Own incident identity, lifecycle, severity, and version | `open()`, `update_status()`, `resolve()` |
| `Alert` | Represent one received alert and its correlation data | `fingerprint()`, `is_duplicate()` |
| `Evidence` | Represent source-backed observations and availability | `is_available()`, `as_citation()` |
| `Finding` | Represent a structured cause, impact, next step, or uncertainty | `validate_confidence()` |
| `TimelineEvent` | Represent an ordered user-visible state change | `display_payload()` |
| `IncidentService` | Coordinate alert intake and incident lifecycle | `accept_alert()`, `get_incident()`, `resolve_incident()` |
| `IncidentRepository` | Persist and retrieve incident aggregates | `save()`, `get_by_id()`, `find_by_fingerprint()` |
| `TimelineRepository` | Persist and read ordered timeline events | `append()`, `list_for_incident()` |

## Connections

`IncidentService` uses `IncidentRepository` and `TimelineRepository`. `Incident` owns the lifecycle rules. `Alert`, `Evidence`, `Finding`, and `TimelineEvent` belong to an incident but remain separately persisted records.

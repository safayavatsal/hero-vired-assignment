# Durable Execution and API Classes

## Classes

| Class | Responsibility | Main methods |
| --- | --- | --- |
| `Job` | Represent durable work, lease, retry count, and status | `lease()`, `retry()`, `complete()`, `fail()` |
| `JobRepository` | Claim and persist durable jobs | `enqueue()`, `claim()`, `complete()`, `fail()` |
| `Worker` | Poll for leased work and dispatch handlers | `run_once()`, `recover_expired_leases()` |
| `JobDispatcher` | Map job types to handlers | `dispatch(job)` |
| `VerificationService` | Check post-action state independently | `verify()` |
| `IncidentRouter` | Map HTTP routes to application services | `create_routes()` |
| `IncidentController` | Validate requests and map service results | `create_alert()`, `get_incident()`, `get_timeline()` |
| `DecisionController` | Handle acknowledgement, reply, approval, and rejection | `acknowledge()`, `reply()`, `approve()`, `reject()` |
| `ActionController` | Return action state and submit decisions | `list_actions()`, `approve()`, `reject()` |

## Connections

`Worker` uses `JobRepository` and `JobDispatcher`. `JobDispatcher` selects `InvestigationHandler`, `ActionHandler`, or a verification handler. Controllers call application services and return read models; they do not contain domain rules.

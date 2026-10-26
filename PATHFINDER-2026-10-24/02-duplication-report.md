# Duplication Report

| Concern | Existing owner | Decision |
| --- | --- | --- |
| Alert validation and fingerprinting | `main-app/backend/app/application/alert_pipeline.py:43` | Reuse through the alert API; do not add storefront-specific incident logic. |
| Incident persistence and deduplication | `main-app/backend/app/adapters/postgres_incident_repository.py:23` | Reuse unchanged. |
| Scenario evidence | `main-app/backend/app/domain/simulator.py:153` | Reuse the checkout dependency scenario for the failed payment. |
| Investigation, paging, and actions | `main-app/backend/app/application/investigation.py:108`, `main-app/backend/app/application/workflow.py:69` | Reuse unchanged except for local email delivery at the existing notification boundary. |

No duplicate queue, database, incident model, or action engine is justified for the demo storefront.

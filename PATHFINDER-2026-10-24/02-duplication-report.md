# Duplication Report

| Concern | Existing owner | Decision |
| --- | --- | --- |
| Alert validation and fingerprinting | `main-app/backend/app/application/alert_pipeline.py:43` | Reuse through the alert API; do not add storefront-specific incident logic. |
| Incident persistence and deduplication | `main-app/backend/app/adapters/postgres_incident_repository.py:23` | Reuse unchanged. |
| Scenario evidence | `main-app/backend/app/domain/simulator.py:153` | Reuse the checkout dependency scenario for the failed payment. |
| Investigation, paging, and actions | `main-app/backend/app/application/investigation.py:108`, `main-app/backend/app/application/workflow.py:69` | Reuse unchanged except for local email delivery at the existing notification boundary. |
| Similar-history retrieval | `main-app/backend/app/application/retrieval.py`, `main-app/backend/app/adapters/postgres_retrieval_repository.py` | Reuse PostgreSQL and the existing investigation evidence model; do not add a vector service or second history store. |
| Optional evidence requests | `main-app/backend/app/application/investigation.py` | Reuse the existing model boundary and evidence providers; validate every request server-side and keep the fixed fan-out as the baseline. |
| Cost and latency readout | `main-app/backend/app/application/observability.py`, `main-app/backend/app/application/investigation.py` | Persist bounded telemetry beside the investigation and request metrics in memory; do not add a separate telemetry backend. |
| Scenario onboarding | `scripts/add-scenario.sh`, `main-app/backend/app/api/simulator.py` | Reuse the scenario registry and canonical alert intake; do not write database rows directly from the script. |
| Monitoring view | `demo-observability/backend/app/main.py`, `demo-observability/frontend/src/App.tsx` | Keep the demo read-only and derive snapshots from the main API; do not create a second incident source of truth. |
| Remediation workflow | `main-app/backend/app/application/workflow.py`, `main-app/frontend/src/app/App.tsx` | Reuse typed actions, durable jobs, attempts, verification, and timeline events; do not add a parallel action engine. |

No duplicate queue, database, incident model, telemetry store, model loop, or action engine is justified for the demo surfaces.

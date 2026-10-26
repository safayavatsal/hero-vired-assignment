# Demo Commerce Flow

```mermaid
flowchart TD
    Store["Storefront<br/>demo-store/frontend/src/App.tsx"]
    Checkout["Synthetic payment API<br/>demo-store/backend/app/main.py"]
    Alert["Create alert<br/>main-app/backend/app/api/incidents.py:33"]
    Normalize["Normalize and fingerprint<br/>main-app/backend/app/application/alert_pipeline.py:43"]
    Persist["Deduplicate and correlate<br/>main-app/backend/app/adapters/postgres_incident_repository.py:23"]
    Console["Incident console polling<br/>main-app/frontend/src/app/App.tsx"]
    Investigate["Queue investigation<br/>main-app/backend/app/application/investigation.py"]
    Fanout["Four fixed evidence tools<br/>logs · metrics · deploys · health"]
    Similar["Fifth source: similar findings<br/>bounded ranked retrieval"]
    Model["Optional bounded model loop<br/>allowlisted re-queries + telemetry"]
    Page["Own and notify<br/>main-app/backend/app/application/workflow.py"]
    Remediate["Approve + queue + verify<br/>explicit human closure"]
    Monitor["Read-only monitoring<br/>demo-observability :8005/:8006"]

    Store --> Checkout
    Checkout -->|"failed payment alert"| Alert
    Alert --> Normalize --> Persist --> Console
    Console --> Investigate --> Fanout --> Similar --> Model --> Page --> Remediate --> Monitor
    Console --> Page
```

## Side effects

- Payment details are handled only by the store API and are not placed in alert payloads.
- Alert intake writes the existing alert, incident, and timeline records.
- Investigation uses the existing durable worker path.
- The four-tool fan-out and deterministic finding run before optional model enrichment; no configured model means no additional loop work.
- Similar-history retrieval, model requests, and telemetry are evidence/readout paths and cannot authorize actions.
- Paging writes delivery attempts and sends a local captured email.
- Approval queues once, verification confirms observed state, and incident closure remains an operator decision.

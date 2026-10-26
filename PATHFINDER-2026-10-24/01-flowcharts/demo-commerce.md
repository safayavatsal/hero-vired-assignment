# Demo Commerce Flow

```mermaid
flowchart TD
    Store["Storefront<br/>demo-store/frontend/src/App.tsx"]
    Checkout["Synthetic payment API<br/>demo-store/backend/app/main.py"]
    Alert["Create alert<br/>main-app/backend/app/api/incidents.py:33"]
    Normalize["Normalize and fingerprint<br/>main-app/backend/app/application/alert_pipeline.py:43"]
    Persist["Deduplicate and correlate<br/>main-app/backend/app/adapters/postgres_incident_repository.py:23"]
    Console["Incident console polling<br/>main-app/frontend/src/app/App.tsx:98"]
    Investigate["Queue investigation<br/>main-app/backend/app/application/investigation.py:108"]
    Page["Create durable page<br/>main-app/backend/app/application/workflow.py:69"]
    Notify["Deliver notification<br/>main-app/backend/app/application/external_boundaries.py:42"]

    Store --> Checkout
    Checkout -->|"failed payment alert"| Alert
    Alert --> Normalize --> Persist --> Console
    Console --> Investigate --> Page --> Notify
```

## Side effects

- Payment details are handled only by the store API and are not placed in alert payloads.
- Alert intake writes the existing alert, incident, and timeline records.
- Investigation uses the existing durable worker path.
- Paging writes delivery attempts and sends a local captured email.

# Domain Data Model

This document shows the durable relationships between the incident workflow entities. Field-level definitions live in the system architecture document.

```mermaid
erDiagram
    INCIDENT ||--o{ ALERT : contains
    INCIDENT ||--o{ EVIDENCE : gathers
    INCIDENT ||--o{ FINDING : produces
    MODEL_RUN ||--o{ FINDING : produces
    INCIDENT ||--o{ PAGE : sends
    INCIDENT ||--o{ DECISION : receives
    INCIDENT ||--o{ ACTION_REQUEST : proposes
    ACTION_REQUEST ||--o{ ACTION_ATTEMPT : runs
    ACTION_ATTEMPT ||--o{ VERIFICATION : confirms
    INCIDENT ||--o{ JOB : schedules
    INCIDENT ||--o{ TIMELINE_EVENT : records

    INCIDENT {
        uuid id PK
        text fingerprint UK
        text service
        text environment
        text severity
        text status
        integer version
    }
    ALERT {
        uuid id PK
        uuid incident_id FK
        text source_event_id UK
        text fingerprint
        jsonb payload
    }
    EVIDENCE {
        uuid id PK
        uuid incident_id FK
        text source_type
        jsonb result
        text availability
    }
    MODEL_RUN {
        uuid id PK
        uuid incident_id FK
        text provider
        text model_name
        text status
    }
    FINDING {
        uuid id PK
        uuid incident_id FK
        uuid model_run_id FK
        text kind
        numeric confidence
    }
    PAGE {
        uuid id PK
        uuid incident_id FK
        text responder
        integer escalation_level
        text status
    }
    DECISION {
        uuid id PK
        uuid incident_id FK
        text decision_type
        text responder
    }
    ACTION_REQUEST {
        uuid id PK
        uuid incident_id FK
        text action_type
        text approval_state
        text idempotency_key UK
    }
    ACTION_ATTEMPT {
        uuid id PK
        uuid action_request_id FK
        integer attempt_number
        text status
    }
    VERIFICATION {
        uuid id PK
        uuid action_attempt_id FK
        boolean successful
        jsonb observed_state
    }
    JOB {
        uuid id PK
        uuid incident_id FK
        text job_type
        text status
        text idempotency_key UK
    }
    TIMELINE_EVENT {
        uuid id PK
        uuid incident_id FK
        text event_type
        bigint sequence_number
    }
```

## Relationship rules

- An incident is the aggregate root for alerts, evidence, findings, pages, decisions, actions, jobs, and timeline events.
- A model run may produce multiple findings, while each finding remains attached to the incident that supplied its evidence.
- An action request may have multiple attempts, but verification belongs to a specific attempt.
- Timeline events provide the user-facing audit sequence without replacing the normalized source tables.

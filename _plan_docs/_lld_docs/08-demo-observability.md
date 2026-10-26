# Demo Observability Classes and Runtime

## Classes

| Class | Responsibility | Main methods |
| --- | --- | --- |
| `ObservabilityBackend` | Map known local services to bounded dashboard profiles and read incident/action state | `dashboard_catalog()`, `incident_snapshot()` |
| `DashboardProfile` | Define labels, targets, trend points, and before/after values for one demo service | data only |
| `ObservabilityFrontend` | Render metric cards, change comparison, action status, and navigation links | `load_snapshot()`, `render_dashboard()` |

## Runtime sequence

```mermaid
sequenceDiagram
    participant U as Operator
    participant C as Incident console
    participant O as Demo observability UI
    participant B as Demo observability API
    participant A as Incident API

    U->>C: Review verified remediation
    C-->>U: Monitoring deep link with incident id
    U->>O: Open service dashboard
    O->>B: Request incident snapshot
    B->>A: Read incident and actions
    A-->>B: Durable state and before/after result
    B-->>O: Bounded metrics and outcome labels
    O-->>U: Compare before/current values
    U->>O: Open incident remediation backlink
    O-->>C: Return to remediation panel
```

The page is intentionally read-only. It demonstrates feasibility for service monitoring and remediation impact while leaving incident truth, action authorization, and persistence in the existing system.

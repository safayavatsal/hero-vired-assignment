# Architecture Documentation

Status: Recorded

## Decision

Document the architecture in four focused Mermaid-based files:

| Document | Responsibility |
| --- | --- |
| System architecture | Runtime boundaries, responsibilities, integrity rules, and complete relational table/field catalog |
| Runtime sequence flow | Alert-to-resolution message order and execution behavior |
| Domain data model | Entity relationships and foreign-key structure |
| Main UI architecture | Incident-console structure and user interaction boundaries |

Keep the complete schema definition in the system-architecture document. Keep the other documents focused on their own diagram type and avoid duplicating detailed field definitions.

## Consequences

- Each architecture concern is easier to review and update.
- Mermaid diagrams remain directly renderable in repository viewers.
- The schema has one authoritative planning location.

# Hero Vired Assignment

Documentation-first design for the incident investigation and response product described in the assignment.

## Repository structure

- `_plan_docs/_features_docs/` — feature plans
- `_plan_docs/_hld_docs/` — high-level architecture, data model, UI architecture, and API catalog
- `_plan_docs/_lld_docs/` — low-level classes, runtime sequence, and UML class diagram
- `_decision_docs/` — recorded architecture and technology decisions
- `_research_refs/` — source assignment and research references

## Start here

- [Feature baseline](_plan_docs/_features_docs/00-feature-baseline.md)
- [System architecture](_plan_docs/_hld_docs/00-system-architecture.md)
- [API catalog](_plan_docs/_hld_docs/03-api-catalog.md)
- [LLD overview](_plan_docs/_lld_docs/00-lld-overview.md)
- [LLD UML class diagram](_plan_docs/_lld_docs/06-lld-system-diagram.md)

The assignment source is available as `FDE-Assignment.docx` at the repository root and under `_research_refs/`.

## Baseline runtime

Start the current foundation with:

```bash
docker compose up --build
```

- API health: `http://localhost:8001/api/v1/health`
- API readiness: `http://localhost:8001/api/v1/readiness`
- Frontend: `http://localhost:8000`

The current slice establishes the API, worker, frontend, and PostgreSQL services. Incident workflows and simulator scenarios are implemented in later feature slices.

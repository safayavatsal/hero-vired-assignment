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

The current slice establishes the API, worker, frontend, PostgreSQL services, deterministic simulator scenarios, a PostgreSQL-backed alert-to-incident pipeline, bounded investigations, persisted paging and approval workflow, typed action execution, and an incident timeline UI.

## Model gateway configuration

Copy `.env.example` to `.env` and set `MODEL_GATEWAY_TOKEN` locally. The default model URL is Groq's Responses endpoint, with `openai_responses` and `openai/gpt-oss-20b`; override `MODEL_GATEWAY_URL`, `MODEL_GATEWAY_FORMAT`, or `MODEL_GATEWAY_MODEL` when using another compatible provider. Optional notification, ownership, and action-executor URLs enable the corresponding external boundaries; when unset, the deterministic local workflow remains active. Docker Compose passes these settings only to the API container. `.env` is ignored by Git and real credentials must never be committed.

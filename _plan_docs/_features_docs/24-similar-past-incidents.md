# Plan Similar Past Incidents

## Goal

Give an investigation bounded context from completed findings without changing the deterministic diagnosis.

## Implementation

- Add deterministic in-process text embeddings and persist one vector per completed finding in PostgreSQL.
- Add `similar_incidents` as the fifth read-only evidence source with a default top-three result limit.
- Require at least two completed incidents in the retrieval corpus before returning ranked context.
- Treat empty, slow, failed, or unavailable retrieval as an uncertainty note only.
- Show statement, category, and resolution in a separate console panel.

## Acceptance checks

- Repeated scenarios return ranked prior findings and exclude the current incident.
- Empty history is unavailable with a clear reason.
- Retrieval failure leaves the deterministic finding byte-identical.
- No model credential or additional service is required.

## Verification

- Focused retrieval tests cover ranking, empty history, and failure isolation.
- Backend suite, frontend tests, production build, migration syntax, and diff checks pass.
- Compose live proof remains pending when the local container runtime is unavailable.

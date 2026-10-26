# Decision 032: Similar past incidents

## Decision

Store deterministic finding vectors beside the existing investigation data and expose ranked historical findings through one additive evidence source named `similar_incidents`. The source returns at most three results by default and excludes the current incident.

## Safety and degradation

- The deterministic finding is computed before retrieval and never cites retrieved context.
- Fewer than two completed incidents in the retrieval corpus produces an unavailable result with a clear reason.
- Empty, slow, failed, or unavailable retrieval produces an uncertainty note and does not fail the investigation.
- Retrieved values pass through the existing masking and citation-bound prompt path before model use.

## Consequences

- The local demo needs only PostgreSQL and pure-Python hashing logic.
- Vector search is bounded in Python over a capped result set; a larger corpus can later move behind a dedicated indexed search boundary.
- The console can show historical statement, category, and resolution without changing existing API paths.

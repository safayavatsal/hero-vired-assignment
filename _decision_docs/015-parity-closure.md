# Parity Closure

Status: Adopted

## Decision

Use the running API, migrations, and tests as the executable contract, then close verified drift against the approved product documents with the smallest compatible changes.

The closure work covers four boundaries:

| Boundary | Decision | Reason |
| --- | --- | --- |
| Evidence provenance | Persist the read-only query, parameters, collection time, duration, and failure beside every evidence result. | Operators need to distinguish an empty result from a slow or failed source. |
| Incident UI | Show severity, last update, and display-safe timeline payloads in the incident view. | The documented review workflow requires enough context to understand what changed. |
| Evaluation | Keep versioned golden cases and add a stable prompt-contract fingerprint check. | Prompt changes must be visible before they alter investigation behavior. |
| Paging context | Include the latest finding summary and suggested next step in page delivery when available. | Responders need the investigation context at the notification boundary. |
| Documentation | Make the API catalog and physical schema describe the implemented contracts. | Reviewers should not need to infer runtime fields from code. |

## Consequences

- Existing response fields remain compatible; evidence gains additive provenance fields.
- Database migrations remain forward-only and restart-safe.
- Timeline payloads are rendered as data, never as controls.
- Provider-backed behavior remains an environment boundary; deterministic local verification stays reproducible without credentials.

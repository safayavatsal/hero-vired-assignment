# Decision 029: Explicit evidence-tool catalog

## Decision

The bounded evidence layer exposes a small catalog for its enabled tools. Each tool declares its source, stable query name, purpose, and enabled state. Completed investigations persist that metadata beside the tool trace, and the console shows the purpose before the implementation name.

## Why

- Makes the evidence boundary understandable to operators and reviewers.
- Gives API clients a stable discovery endpoint without exposing provider credentials or internal implementation details.
- Keeps tool failures visible through the existing availability and duration fields.
- Reuses the current four-tool boundary instead of introducing a plugin system.

## Consequences

- The catalog is intentionally read-only and small.
- Investigation results remain backward-compatible because the new fields are additive JSON fields.
- Adding a new evidence source requires one catalog entry and its provider implementation.
- Tool metadata explains what was attempted; it does not grant permission to execute remediation.

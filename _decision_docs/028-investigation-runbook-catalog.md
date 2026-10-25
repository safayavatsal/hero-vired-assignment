# Decision 028: Scenario-owned investigation runbooks

## Decision

Each investigation scenario owns a short, ordered runbook in its public scenario definition. Every step contains only an identifier, a title, and a plain-language purpose. The console renders the runbook before work starts, marks it active while the worker is running, and marks it complete with the finding.

## Why

- Makes the investigation explainable before a reviewer starts it.
- Keeps the checklist aligned with the selected service and scenario.
- Gives the local demo a visible path from incident to finding without exposing internal implementation details.
- Allows future data-defined scenarios to describe their bounded checks without adding UI-specific code.

## Consequences

- Scenario definitions become the source of truth for the visible investigation checklist.
- The checklist explains bounded checks; it does not authorize actions or replace human approval.
- Custom scenario validation now rejects incomplete runbook steps.
- The UI remains intentionally small: one checklist state is derived from the existing investigation lifecycle.

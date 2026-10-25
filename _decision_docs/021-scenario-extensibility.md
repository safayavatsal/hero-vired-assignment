# Scenario Extensibility

Status: Adopted

| Area | Decision | Reason |
| --- | --- | --- |
| Scenario shape | A scenario carries its own finding rule (metric, category, statement, confidence, next step, cited sources). | New scenarios become data; the investigation pipeline stays untouched. |
| Matching | The investigation service matches rules against collected metric evidence generically. | One code path serves every scenario; uncertainty, degradation, and contradiction handling apply automatically. |
| Generic rules | A small registry covers reusable metric shapes (for example queue depth) across scenarios. | A newly registered scenario works even when it reuses a known metric pattern. |
| Registration | The existing simulator scenario endpoint accepts an optional definition and registers it at runtime. | Keeps the documented add-or-select contract and supports live-session scenario additions. |
| Persistence | Registered scenarios are stored in simulator state and reloaded on restart. | A scenario added during a session is not lost. |
| Safety | Built-in scenarios cannot be replaced; definitions are validated before use; hidden causes never appear in public listings. | Demo integrity and the existing privacy boundary are preserved. |
| UI | The console derives scenario names, services, and action types from the public scenario listing. | The UI supports new scenarios without frontend changes. |

## Consequences

- Adding a scenario is one declarative payload: evidence, controls, allowed actions, and its finding rule.
- Deterministic finding behavior stays versioned through the golden evaluation cases and the prompt contract hash.
- The generic rule registry remains intentionally small; scenario-specific behavior belongs in scenario data.

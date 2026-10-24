# 017 — Assignment Flow Parity Closure

## Decision

The assignment flow is complete only when every supported scenario has an explicit end state, every human response remains actionable at the correct point, and the UI exposes the same state transitions as the API.

| Concern | Decision |
| --- | --- |
| Investigation lifecycle | Record both start and completion in the incident timeline. |
| Local remediation | Mark the incident resolved only after service-state verification succeeds. |
| External dependency | Mark the incident unfixable and show that no local action is available. |
| Human follow-up | Keep reply and further-investigation controls usable after acknowledgement or reply. |
| Evidence of parity | Verify backend tests, frontend tests/build, Docker execution, and live scenario outcomes together. |

## Consequences

- Operators can distinguish a completed fix from an incident that requires external escalation.
- Timeline records explain why the workflow stopped or closed.
- The UI cannot offer a misleading local action for an unfixable scenario.
- Broader capability and code-structure comparison remains a separate follow-up after assignment-flow parity is proven.

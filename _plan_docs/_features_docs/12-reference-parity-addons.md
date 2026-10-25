# Plan Reference Parity Add-ons

## Goal

Close the six capability differences identified by the function-level comparison only when the project owner approves the corresponding product expansion.

## Ordered work

1. Define a small analyzer/tool registry contract with explicit enablement, failure state, and result normalization.
2. Add an iterative investigation step model with bounded tool calls, cancellation, and durable intermediate state.
3. Add provider-neutral conversation continuation and optional streamed progress events.
4. Add operational telemetry for model latency, token/cost metadata, tool failures, and provider refresh state.
5. Add one additional resource-family analyzer only after the registry and normalized failure contract are accepted.
6. Add focused fixtures and evaluation cases for each approved analyzer and interaction path.

## Acceptance checks

- Every enabled analyzer has a typed contract, failure behavior, and focused test.
- Investigation steps remain bounded, auditable, idempotent, and safe to retry.
- Progress events never replace the durable final investigation result.
- Provider and telemetry failures remain visible without fabricating findings.
- New resource coverage does not change the existing scenario results.

## Implementation status

The first approved add-on is implemented: scenario definitions now expose a bounded, data-owned investigation runbook, and the console renders its progress from the existing investigation lifecycle. The second approved add-on is also implemented: the bounded evidence layer exposes an explicit tool catalog, persists purpose/enabled metadata in investigation traces, and shows that purpose in the console. The third approved add-on is implemented: a separate read-only resource analyzer surface exposes six named analyzers, explicit filters, normalized findings, and a discoverable API without changing the existing incident workflow.

Verification: Docker images built successfully, the backend suite returned 70 passing tests after the analyzer addition, the focused analyzer suite returned 8 passing tests, the frontend suite returned 6 passing tests, the production frontend build passed, the live Docker analyzer API returned all six analyzers and a normalized Pending-Pod finding, and browser verification confirmed the dedicated Kubernetes health tab and sample scan while the existing incident workflow remained intact.

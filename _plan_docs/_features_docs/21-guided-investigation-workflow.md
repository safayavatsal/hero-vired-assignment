# Plan Guided Investigation Workflow

## Goal

Make the browser workflow explain the difference between investigation context, human ownership, and approved remediation.

## Problem

The simulator needs a scenario identifier to select bounded evidence and deterministic expectations, but presenting that identifier as the first operator decision makes it look like the operator is choosing the diagnosis.

## Steps

1. Derive and display the matching investigation context from the selected incident service by default.
2. Keep context changes available only as an explicit advanced option for controlled demo runs.
3. Explain that notifying and acknowledging the service owner records human ownership, not resolution.
4. Explain that remediation is proposed, approved, queued, executed, and verified in order.
5. Preserve the no-local-fix path for external dependency incidents.

## Acceptance checks

- The default screen does not present a scenario dropdown as the primary investigation action.
- A reviewer can see why the context was selected and can still use a controlled override.
- Owner notification and acknowledgement have distinct plain-language meanings.
- The remediation section makes human approval and post-action verification explicit.
- Existing API contracts, sequential gating, and scenario matching remain unchanged.

## Status

Implemented in the incident console and documented in the demo runbook.

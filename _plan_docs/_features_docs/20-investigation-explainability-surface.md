# Plan Investigation Explainability Surface

## Goal

Make the browser investigation view explain how the conclusion was produced without exposing raw payloads by default.

## Steps

1. Present the structured investigation as three plain-language sections: current condition, likely cause, and next step.
2. Show provider status, selected model, and response time when telemetry is available.
3. Show every bounded evidence query with its source, status, duration, and evidence identifier.
4. Keep parameters, degraded-source notes, and raw payloads available as opt-in review details.

## Acceptance checks

- A reviewer can understand the finding before opening raw evidence.
- A reviewer can see which source queries ran and whether any were degraded.
- Model and deterministic findings remain visibly distinct.
- The existing sequential investigation, response, approval, execution, and verification flow is unchanged.
- Frontend tests, production build, diff checks, and the local submission verifier pass.

## Status

Implemented for the local assignment workflow.

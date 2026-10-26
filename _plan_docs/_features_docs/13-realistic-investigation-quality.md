# Plan Realistic Investigation Quality

## Goal

Make the local assignment feel like a usable on-call product for a small e-commerce system while keeping the existing safety and workflow contract intact.

## Ordered work

1. Enrich the three simulator scenarios with realistic order, payment, checkout, worker, request, deployment, and dependency evidence without exposing the hidden cause in the scenario catalog.
2. Introduce a small evidence-tool registry so every bounded investigation query has a name, parameters, availability, duration, and auditable result.
3. Persist investigation tool traces and model-call metadata without credentials or raw provider responses; keep deterministic findings as the safe fallback.
4. Present the structured model analysis and investigation progress in the React workflow, remove duplicate responder content, and keep human approval as the action gate.
5. Add focused scenario tests and run the backend, frontend, build, Compose, and static checks before updating the project records.

The local model mode provides a contract-valid no-secret path for demonstrations while preserving the optional remote gateway boundary.

## Success checks

- A fresh scenario investigation contains concrete e-commerce evidence and valid citations.
- Every evidence query appears in a bounded trace with success or degraded status.
- Provider metadata is visible without exposing tokens or untrusted raw responses.
- The UI distinguishes deterministic findings, model analysis, degraded evidence, and pending work.
- The responder workflow appears once and remains sequential: investigate, respond, approve, execute, verify.
- Docker/PostgreSQL tests, frontend tests, frontend build, Compose validation, and restricted-reference scans pass.

## Boundaries

- Hosted provider credentials and hosted deployment behavior are excluded from this local proof.
- No autonomous action is added; typed actions still require human approval.
- Conversation streaming and broader resource-family coverage remain follow-up work after this five-task slice, because the assignment’s required local workflow already uses durable polling and three scenarios.

## Status

Complete for the local assignment workflow. The Docker/PostgreSQL suite returned 49 passing tests, the frontend smoke suite and production build passed, Compose validation passed, the restricted-reference scan was empty, and the refreshed browser UI confirmed the guided investigation path and model readout.

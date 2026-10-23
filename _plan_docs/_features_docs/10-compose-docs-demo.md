# Plan Compose Documentation And Demo

## Goal

Make the complete baseline easy to run, inspect, and demonstrate.

## Steps

1. Define backend, frontend, and persistence services in the Compose file.
2. Add health checks and startup ordering.
3. Add one-command seed/reset behavior.
4. Document setup, environment variables, scenario triggers, human responses, and expected outcomes.
5. Document the architecture tour and failure-mode controls in the README.
6. Write the required decision summary and AI usage record.
7. Preserve meaningful commits as the implementation progresses.
8. Add a demo script or command sequence covering all scenarios and one failure-mode path.
9. Verify the live-change path by adding a small scenario or analyzer without restructuring the system.

## Implementation status

Implemented locally. Compose now has safe defaults for a clean checkout when `.env` is absent, while preserving `.env` overrides. `scripts/demo.sh` exercises all three scenarios and a degraded evidence path, `scripts/reset-demo.sh` restores the demo state, and a focused queue-pressure analyzer test verifies the small live-change workflow without changing the architecture.

## Acceptance checks

- A clean environment starts with `docker compose up`.
- Every scenario is triggerable from documented commands.
- A reviewer can follow the complete incident timeline.
- Required repository documents and tests are present.

## Verification

- `docker compose config -q` passes with and without local environment overrides.
- The backend Docker suite covers the demo and live-change regression path.
- Frontend smoke tests and the production build pass.
- Documentation describes setup, environment variables, scenario triggers, human responses, expected outcomes, and reset/demo commands.

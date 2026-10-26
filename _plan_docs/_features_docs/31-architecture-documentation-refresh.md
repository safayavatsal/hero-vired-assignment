# Architecture Documentation Refresh

## Goal

Keep the dated Pathfinder packet, HLD, LLD, and rendered architecture map aligned with the current application boundaries and implemented feature set.

## Scope

- Update Pathfinder feature ownership, flow, duplication decisions, and handoff guidance.
- Add a current-state review guide for the main app, demo store, and demo observability surfaces.
- Update HLD runtime and UI boundaries for scenario onboarding, historical retrieval, bounded model evidence, telemetry, remediation, and monitoring.
- Update LLD package, class, investigation, and runtime-sequence documentation.
- Regenerate the architecture HTML from its source JSON and verify repository evidence.

## Acceptance checks

- Pathfinder paths point to `main-app/`, `demo-store/`, and `demo-observability/` correctly.
- HLD and LLD describe the fixed evidence path, optional bounded loop, persisted telemetry, explicit remediation closure, and read-only monitoring boundary.
- Architecture JSON and rendered HTML have matching current repository evidence.
- Architecture validation passes all showcase checks with zero warnings.
- Documentation diff has no whitespace errors or stale primary-app paths.

## Status

Implemented locally. The source architecture map validates and delivers with 9/9 showcase checks, zero errors, zero warnings, and 16 verified repository references. Automated browser visual-check was skipped because no Chrome or Chromium executable was available.

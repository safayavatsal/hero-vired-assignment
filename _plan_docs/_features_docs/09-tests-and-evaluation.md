# Plan Tests And Evaluation

## Goal

Prove the high-risk behavior and detect investigation regressions.

## Steps

1. Add unit tests for normalization, fingerprints, correlation, state transitions, and idempotency.
2. Add simulator tests for each scenario and each failure control.
3. Add investigation tests for evidence citations, missing sources, contradictions, unfixable incidents, and unsafe text.
4. Add paging tests for acknowledgement, reply, approval, rejection, delivery failure, timeout, and escalation.
5. Add action tests for approval binding, duplicate requests, timeout-after-success, verification, and restart recovery.
6. Add API and UI tests for incident listing, timeline rendering, and human decisions.
7. Create golden investigation cases with expected causes, evidence IDs, confidence bounds, and safe next steps.
8. Version prompts and compare evaluation results and the prompt contract fingerprint before accepting changes.

## Implementation status

Implemented locally. The existing focused suite covers alert, simulator, investigation, paging, action, worker, API-health, and UI-selection behavior. A committed golden evaluation set now checks all three scenarios for expected diagnosis, safe next step, confidence bounds, required evidence sources, valid citations, and prompt-version alignment.

## Acceptance checks

- All three scenarios pass from alert through resolution or unfixable classification.
- Failure-mode tests pass deterministically.
- Prompt changes report accuracy, citation, and safety differences.
- The test suite runs from the Compose environment.

## Verification

- The Docker/PostgreSQL backend suite returned 49 passing tests with no warnings.
- Golden evaluation cases cover deployment regression, disk pressure, and third-party outage, including the active prompt contract fingerprint.
- The frontend smoke suite remains green with 5 passing tests and the production build passes.
- The suite also checks realistic e-commerce evidence fields, tool trace metadata, persisted model telemetry, and structured model analysis.

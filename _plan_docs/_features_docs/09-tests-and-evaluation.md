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
8. Version prompts and compare evaluation results before accepting changes.

## Acceptance checks

- All three scenarios pass from alert through resolution or unfixable classification.
- Failure-mode tests pass deterministically.
- Prompt changes report accuracy, citation, and safety differences.
- The test suite runs from the Compose environment.

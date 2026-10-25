# Assignment Parity Analysis

Internal research note. Keep implementation-neutral; do not name external products.

## Method

The assignment document was analyzed requirement by requirement and compared against the implemented product. Three mature open-source systems in the same problem space (AI incident diagnosis, automated Kubernetes diagnostics, and an agent-based remediation engine) were studied for patterns that map onto the assignment's on-site demands.

## Requirement coverage

| Assignment requirement | Status in this project |
| --- | --- |
| Alerts as incidents you can track | Covered: canonical webhook intake, dedup, correlation, durable incidents. |
| LLM + tools investigation with cited summary | Covered: bounded evidence tools, deterministic findings, validated model readout, citation enforcement. |
| Paging the right person, sensible escalation | Covered: ownership resolution, delivery attempts, ack/reply/timeout, fallback escalation, overdue recovery. |
| Human-approved actions carried out | Covered: typed allowlist, approval expiry, idempotent execution, attempts, verification. |
| React UI with incident list and timeline | Covered: guided console with ordered audit timeline. |
| One `docker compose up` | Covered. |
| Duplicate/late/out-of-order/flapping alerts | Covered and exercised by demo scripts. |
| Slow/down evidence sources | Covered: per-source timeouts and availability recorded as evidence. |
| Actions timing out after completion | Covered: timeout is an explicit state; verification uses the persisted result. |
| Escalation when a responder is silent | Covered. |
| Untrusted log text | Covered: masking before model use, validated citations, no execution from text. |
| Unfixable third-party outage | Covered: explicit `unfixable` terminal state, no local action. |
| Deploys during incidents; nothing lost or done twice | Covered: durable jobs, leases, idempotency keys, restart recovery. |
| LLM cost/rate limits | Covered: unconfigured/degraded model path, prompt bounding, concurrency caps. |
| Prompt quality regression detection | Covered: versioned golden evaluation cases pinned to a prompt contract hash. |

## Gaps found and actions taken

1. **Live scenario addition (highest risk).** The on-site session requires adding described incidents in minutes. Scenarios were code in three places (simulator definitions, analyzer chain, frontend maps). Resolution: finding rules moved into scenario data, a generic rule matcher, runtime scenario registration through the existing endpoint, and a UI that derives everything from the public scenario listing (decision 021, feature 16).
2. **Documented add-or-select contract was only select.** The API catalog promised scenario addition; the endpoint now honors it.
3. **Smaller observations.** Per-run model telemetry already exists; the auto-action policy question is answered by decision 006 (nothing runs without a human) and should be stated explicitly in the delivery documents rather than changed.

## Patterns adopted from the reference systems

- Registry-of-data extensibility instead of per-alert-type code branches.
- The LLM treated as an optional enrichment pass that never gates deterministic results.
- Fail-closed approval gating with decision records bound to the exact approved action.
- Per-run cost/status telemetry attached to every investigation.
- Sensitive-token masking before any model or external call.

## Remaining optional improvements

- Consider exposing investigation prompt text itself for on-site discussion of prompt quality.
- Optional: a recorded demo of registering a new scenario live, for rehearsal.

The submission summary now covers the million-user scaling question, and malformed structured model output is rejected at the model boundary.

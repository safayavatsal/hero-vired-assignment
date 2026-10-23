# Plan Paging And Human Response

## Goal

Deliver actionable incidents to the right person and handle non-response.

## Steps

1. Resolve the primary responder from service ownership and severity.
2. Create a page containing incident identity, impact, evidence summary, suggested next step, and response options.
3. Record delivery attempts and their outcomes.
4. Accept acknowledgement, free-form reply, approval, rejection, and explicit request for more investigation.
5. Start a configurable response deadline after delivery.
6. Escalate to the fallback responder after timeout and record the reason.
7. Prevent duplicate pages for the same incident and escalation level.
8. Make the page and all responses visible in the incident timeline.

## Acceptance checks

- A primary responder can acknowledge and respond.
- A non-responsive responder causes exactly one fallback escalation.
- Approval and rejection are tied to the current action proposal.
- Delivery failure does not erase the incident.

## Implementation status

Implemented:

- Durable primary and fallback page records.
- Acknowledgement and reply responses.
- One-time timeout escalation to a fallback responder.
- Page delivery, response, timeout, and escalation timeline events.
- Timeline writes lock the incident row before allocating the next sequence number.

Verified locally through Docker/Postgres on 2026-10-22: acknowledgement persisted, timeout created one delivered fallback, retry returned the escalated primary, and the page list contained exactly two records for the timeout scenario.

Implemented:

- Optional ownership lookup resolves primary and fallback responders when page responders are omitted.
- Optional notification delivery receives a page payload and records an external delivery identifier in the timeline.
- Page delivery includes the latest finding's evidence summary and suggested next step when an investigation is available.
- Missing external configuration keeps the deterministic local paging behavior.
- Page delivery attempts are persisted for primary and fallback pages.
- The worker checks overdue pages during polling and creates one fallback page without duplication.

Boundary verification:

- Configured notification and ownership calls are covered by adapter contract tests and a real localhost HTTP integration test; hosted deployment verification is out of scope for this local test assignment.

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

Open:

- External notification delivery and service-ownership lookup.

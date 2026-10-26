# Main UI Architecture

This document describes the main incident-console structure. It focuses on user-visible composition and interaction boundaries, not backend execution order.

```mermaid
flowchart TB
    App[Incident console]
    List[Incident list]
    Detail[Incident detail]
    Summary[Current condition and likely cause]
    Evidence[Evidence references]
    Timeline[Ordered incident timeline]
    Decisions[Human decisions]
    Actions[Approved actions and verification]
    Store[Separate demo store frontend]

    Store -->|payment failure alert| App
    App --> List
    App --> Detail
    Detail --> Summary
    Detail --> Evidence
    Detail --> Timeline
    Detail --> Decisions
    Detail --> Actions
    Decisions -->|acknowledge| Detail
    Decisions -->|reply| Detail
    Decisions -->|approve or reject| Detail
    Actions -->|result and verification| Timeline
    Actions -->|explicit close| Detail
    Detail -->|finding discovers category| Decisions
    Decisions -->|notify owner or claim locally| Detail
    Actions -->|approve and queue once| Actions
    Actions -->|persistent before and after state| Timeline
```

## UI data boundaries

| UI area | Reads | Writes |
| --- | --- | --- |
| Incident list | Incident summary, severity, status, updated time | None |
| Incident detail | Summary, evidence, findings, pages, decisions, actions, timeline | Acknowledge, reply, approve, reject, close |
| Timeline | Ordered display-safe timeline events | None |
| Action panel | Typed action request, approval state, attempts, verification | Approval or rejection only |
| Demo store | Catalog, cart, synthetic payment fields, payment result | Store payment API only |

## UI rules

- Every user action shows its backend result and the next state returned by the API.
- Evidence is displayed with its source, query, availability, observation time, and relationship to the finding.
- Approval controls show the exact action type, target, parameters, and expiry before submission.
- Action completion is shown only after simulator execution and verification are persisted.
- Polling refreshes the incident detail and timeline without clearing the selected incident's open sandbox preview.
- Verification shows before/after evidence and a direct incident link; the operator closes the incident explicitly.
- A failed synthetic checkout links directly to its accepted incident; the separate store backend strips payment fields before emitting the operational alert.

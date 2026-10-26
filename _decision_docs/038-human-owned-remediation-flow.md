# Decision Human-Owned Remediation Flow

## Decision

The investigation result is the only source for the displayed category and recommended local action. The operator may notify a specific owner or claim the incident locally. Approval is one browser action that records the decision and queues the typed work; the execution state and before/after result remain visible until verification.

## Safety

- Scenario analyzer rules remain server-side and are not exposed as precomputed diagnosis in the public scenario listing.
- Email recipients are validated at the API boundary and stored with the page record.
- Self-ownership skips delivery but still creates a durable acknowledged page and timeline event.
- The existing typed action, approval, idempotency, worker, and verification boundaries remain authoritative.

## Consequences

The browser has fewer ambiguous controls and no duplicate queue step. Existing clients can still call the execute endpoint. Recipient persistence adds one nullable page column; process identity remains a local operator until a real identity boundary is added.

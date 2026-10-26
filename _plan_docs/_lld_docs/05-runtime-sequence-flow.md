# Runtime Sequence Flow

This document describes the alert-to-resolution runtime sequence. It is intentionally separate from the high-level system architecture because it shows message order, retries, human decisions, action execution, and verification.

```mermaid
sequenceDiagram
    participant S as Simulator or alert source
    participant A as API
    participant D as PostgreSQL
    participant W as Worker
    participant M as Model adapter
    participant P as Paging boundary
    participant H as Human responder
    participant U as React UI

    S->>A: Send alert webhook
    A->>D: Validate, fingerprint, and persist alert
    D-->>A: Existing or new incident
    A->>D: Enqueue investigation job
    A-->>S: Accepted with idempotent result
    W->>D: Claim investigation job with lease
    W->>S: Query fixed logs, metrics, deploys, and health sources
    S-->>W: Evidence or bounded failure
    W->>D: Index completed finding vector
    W->>R: Query ranked similar completed findings
    R->>D: Search bounded finding vectors
    D-->>R: Historical context or empty result
    R-->>W: Similar-incidents evidence or uncertainty
    W->>M: Submit masked five-source evidence context
    M-->>W: Validated findings, citations, or bounded request
    alt Model requests more evidence
        W->>S: Execute allowlisted re-query
        S-->>W: Additional bounded evidence
        W->>M: Re-submit context with new evidence
        M-->>W: Validated findings and citations
    end
    W->>D: Persist evidence, findings, trace, telemetry, and timeline events
    W->>P: Send page
    P-->>H: Deliver incident notification
    H->>A: Acknowledge or reply
    A->>D: Persist human decision and timeline event
    H->>A: Approve or reject typed action
    A->>D: Validate decision and enqueue action job
    W->>D: Claim action job with lease
    W->>S: Execute approved typed action
    S-->>W: Operation result, timeout, or unknown outcome
    W->>S: Verify current state independently
    S-->>W: Verification evidence
    W->>D: Persist attempt, verification, and resolution state
    U->>A: Poll incident and timeline
    A-->>U: Ordered backend truth
```

## Runtime guarantees

- Duplicate, late, and out-of-order alerts are accepted safely through source keys, fingerprints, and event ordering.
- A synthetic checkout failure uses the same alert webhook and keeps payment fields outside the incident boundary.
- A slow or unavailable evidence source produces a bounded evidence state rather than an invented result.
- Historical retrieval is optional context; empty, slow, or failed retrieval becomes an uncertainty note only.
- The model loop ends on its round, request, evidence-item, or wall-clock bound and records the stop reason instead of raising.
- Source timings, retrieval latency, token estimates, and estimated cost are persisted with the investigation.
- A human approval is checked again when the worker claims the action job.
- An action timeout leads to verification before any success or resolution state is recorded.
- The UI reads the durable incident state and timeline; it does not treat an optimistic request as completed work.

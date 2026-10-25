# Decision Guided Investigation Workflow

## Decision

Present the incident’s matching scenario as read-only investigation context by default, keep a controlled override behind an advanced option, and describe the workflow using operator intent.

| Area | Decision | Consequence |
| --- | --- | --- |
| Investigation context | Match the context to the incident service and keep manual changes advanced-only. | The operator reads the result as a system diagnosis instead of a manually selected answer. |
| Owner coordination | Call the step `Notify the service owner` and explain that acknowledgement records ownership. | Paging, acknowledgement, and replies are easier to distinguish from remediation. |
| Remediation | Call the step `Approve and verify remediation` and show the state transitions in order. | Human approval remains visible before queueing and verification. |
| External dependency | Keep the `No local fix` path separate from local actions. | The UI does not suggest an unsafe or impossible remediation. |

## Boundary

The API still receives an explicit scenario identifier because the local simulator uses bounded scenario definitions. This decision changes the operator presentation without changing the investigation, persistence, or safety contracts.

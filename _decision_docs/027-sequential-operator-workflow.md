# Decision Sequential Operator Workflow

## Decision

Treat investigation, ownership, and remediation as separate operator states. A completed investigation is a result, not an invitation to rerun; a deeper pass is an explicit secondary action; acknowledgement closes ownership and unlocks remediation review.

| Area | Decision | Consequence |
| --- | --- | --- |
| Completed investigation | Keep the finding visible and remove the normal rerun button. | The operator reads the finding before taking another action. |
| Deeper analysis | Use a distinct `deeper` investigation mode from the result view. | A deliberate follow-up is possible without confusing it with the first run or silently reusing cached output. |
| Ownership | Allow an optional owner note before acknowledgement and close the step after acknowledgement. | The next valid action is clear: review the recommendation. |
| Remediation explanation | Show the likely cause, current condition, and evidence citations before proposal or approval. | The human can judge why the action is recommended. |
| Remediation review | Preview the action as a read-only before/after projection before creating the approval decision. | “Review” has observable meaning and cannot mutate service state. |
| Notification recipient | Prefer the resolved owner address, then the configured local owner address, then a responder-specific local address. | Captured notifications represent a particular owner rather than a generic shared inbox. |

## Boundary

The existing page response API remains compatible for audit and integration clients. The browser’s primary path now uses acknowledgement for ownership and the investigation API’s explicit deeper mode for follow-up analysis.

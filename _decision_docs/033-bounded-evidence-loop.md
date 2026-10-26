# Decision 033: Bounded evidence loop

## Decision

After the fixed evidence collection and deterministic finding, a configured model may request bounded read-only evidence from the server-side allowlist. Allowed requests are `similar_incidents` and re-queries for the four existing sources. The server chooses the actual tool and ignores model-supplied execution details.

## Bounds

- Additional requests default to two.
- Model rounds default to three total.
- Additional evidence is capped by a total item count and a wall-clock budget.
- Every additional result receives a normal evidence identifier and is included in the next citation validation set.

## Consequences

- The no-model path remains the fixed fan-out path.
- Invalid or disallowed requests are recorded and skipped.
- Reaching any bound ends the loop with telemetry instead of an exception.

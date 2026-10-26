# Decision 036: Local operator roles

## Decision

Add a small server-side bearer-token role boundary for operator mutations. The boundary is disabled by default for the local assignment path and becomes required when `AUTH_MODE=required` with an `OPERATOR_TOKENS` mapping.

Roles are ordered from least to most privileged: `viewer`, `responder`, `approver`, and `administrator`. Investigations, paging, and action proposals require a responder; action decisions and execution require an approver; unknown-action reconciliation requires an administrator.

## Safety boundary

- Tokens are read only from environment configuration and are never returned by the API.
- Missing, malformed, or insufficient credentials produce generic 401, 403, or 503 responses.
- Disabled authentication preserves the existing local demo and is not a production identity claim.
- A future identity provider can replace the token resolver without changing route permissions.

## Consequences

- The API has an explicit authorization seam for the operator workflow.
- The default Compose demo remains backward-compatible.
- Full login, session management, rotation, and tenant-scoped identity remain outside this assignment slice.

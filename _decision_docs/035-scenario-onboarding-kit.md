# Decision 035: Scenario onboarding kit

## Decision

Use one standard-library shell command as the presenter-facing path for registering a scenario and triggering its first alert. Keep validation in the script aligned with the server contract, then let the existing API remain the final authority.

## Safety and limits

- The command sends one alert and extracts the accepted incident identifier from the response.
- It validates the JSON shape, required finding fields, confidence range, and runbook shape before making requests.
- The default backend is `http://localhost:8001`; `BASE_URL` is the only runtime override.
- No credentials, new container, or additional package is required.

## Consequences

- A new scenario can be demonstrated without editing source code.
- The first incident is immediately available for console investigation.
- Server-side validation remains authoritative if the script and API rules diverge.

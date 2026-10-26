# Plan Scenario Onboarding Kit

## Goal

Give presenters and reviewers one safe command for adding a data-defined scenario and creating its first incident.

## Implementation

- Add a standard-library shell script that validates a scenario JSON file.
- Register the definition through the existing simulator endpoint.
- Trigger exactly one alert through the existing incident intake path.
- Print the accepted incident identifier and document the workflow in one page.

## Acceptance checks

- Invalid JSON and incomplete definitions fail before registration.
- A valid definition produces one registration request and one alert request.
- The script prints the created incident identifier.
- The guide covers the JSON shape, local command, port override, and UI follow-up.

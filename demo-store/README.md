# Demo Store

This standalone local application makes the incident workflow demonstrable from a customer action.

- `frontend/` serves the catalog, cart, checkout, and payment result on host port `8003`.
- `backend/` serves the catalog and synthetic payment API on host port `8004`.
- An approved test card returns a synthetic order identifier and creates no incident.
- A declined test card sends a privacy-bounded failure alert to the on-call API and returns the created incident identifier.

Start the complete project from the repository root with `docker compose up --build`, then open `http://localhost:8003`.

Only the two card numbers displayed by the frontend are supported. This application does not process or persist real payment data.

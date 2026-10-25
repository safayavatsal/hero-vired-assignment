# Demo Store

This standalone local application makes the incident workflow demonstrable from a customer action.

- `frontend/` serves the catalog, cart, checkout, and payment result on host port `8003`.
- `backend/` serves the catalog and synthetic payment API on host port `8004`.
- An approved test card returns a synthetic order identifier and creates no incident.
- A declined test card returns a customer-safe payment reference. Its embedded observer independently sends a privacy-bounded failure event to the on-call API.
- The homepage also exposes three customer journeys: slow checkout after a release, delayed fulfillment from worker disk pressure, and provider-unavailable checkout.

Start the complete project from the repository root with `docker compose up --build`, then open `http://localhost:8003`.

Only the two card numbers displayed by the frontend are supported. This application does not process or persist real payment data.

The storefront does not link to internal operational tools. Operators use the incident console separately to inspect the resulting checkout incident.

The two non-payment journeys use `POST /api/store/scenarios/{scenario_id}` with an attempt identifier and product IDs. The response is customer-safe and includes the resulting incident identifier for local demo verification; the observer payload contains no card fields.

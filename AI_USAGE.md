# AI Usage

## Deliberately authored work

The project is being developed as peer programming. The project owner directs and approves the design; implementation logic is AI-assisted and reviewed against that design.

## Deliberately authored work

The following work is deliberately authored and reviewed as project design work:

- The high-level design decisions and architecture boundaries.
- The low-level design structure, class responsibilities, methods, variables, and relationships.
- The LLD structure decision and the consolidated decision index.
- The API catalog organization and documentation structure.
- The baseline runtime boundaries and service responsibilities.
- The class-level LLD and the relationships between its classes.



## AI-assisted implementation

The baseline runtime wiring, service configuration, health endpoints, worker process, and frontend shell were implemented with AI assistance from the approved design.

The simulator service, scenario definitions, evidence queries, typed actions, timeout state, verification endpoint, and focused tests were implemented with AI assistance from the approved simulator plan.

The alert normalization, fingerprinting, duplicate handling, incident correlation, timeline ordering, incident read APIs, and focused tests were implemented with AI assistance from the approved alert-pipeline plan.

The PostgreSQL repository, schema initialization, transactional alert persistence, idempotent delivery handling, and restart-safe incident reads were implemented with AI assistance from the approved incident-state plan.

The explicit incident transition validation, optimistic version check, transition endpoint, and transition timeline records were implemented with AI assistance from the approved incident-state plan.

The bounded evidence collection, deterministic scenario analyzers, finding schema, citation validation, investigation API, and focused tests were implemented with AI assistance from the approved investigation plan. Model analysis remains deliberately unconfigured in this slice.

The investigation repository, durable evidence and finding records, restart-boundary test, and unavailable-source handling were implemented with AI assistance from the approved investigation plan.

The model gateway boundary, sensitive-value masking, structured-response validation, citation checks, and safe model failure statuses were implemented with AI assistance from the approved investigation plan. No provider credential is stored in the repository.

The simulator restart state, delivery delay/order controls, action idempotency, correlation-window lookup, restart-safe investigation reuse, and structured-output provider adapter were implemented with AI assistance from the approved Feature 1–4 plans. The project owner remains responsible for the design boundaries and review of these changes.

The durable paging, fallback escalation, typed approval workflow, simulator execution boundary, audit timeline events, and incident timeline UI were implemented with AI assistance from the approved paging, action, and UI plans. The human-authored workflow boundary remains explicit: provider text cannot execute actions, and approval is required before execution.

The project owner directed and reviewed the live Docker/Postgres verification for Features 5–7. The verification confirmed readiness, the full backend test suite, page acknowledgement, fallback escalation, approved simulator action execution, post-action verification, timeline persistence, retry safety, and frontend availability. No external notification provider or configured model credential was used in this check.

The evidence review surface was implemented with AI assistance from the UI plan. It loads persisted investigations, renders findings, confidence, uncertainty, citations, source availability, timestamps, and masked evidence payloads. The project owner remains responsible for deciding which evidence is safe and useful to expose.

The configurable external-boundary adapters were implemented with AI assistance from the paging and action plans. They keep local behavior when URLs are absent, forward only bounded payloads when configured, validate responses, and never allow an external or model response to bypass approval or backend action validation.

## Issues Caught

The project owner identified these implementation issues during verification:

- The frontend build lacked React type declarations. The fix added the required type dependencies and Vite environment declaration.
- The backend container reported zero tests because the image excluded `tests/`. The Dockerfile was corrected to include the test suite.
- The repository review identified that the UI could propose an invalid action for a selected scenario. The fix validates scenario/action/target combinations before approval and makes the UI show only the allowed local action.
- The project owner identified that the five-second incident refresh reselected the first incident after a service was clicked. The fix preserves the selected incident ID across refreshes so each service opens its own incident and description.
- The review identified and the project owner directed fixes for five follow-up issues: timeline writes now serialize sequence allocation, stale frontend detail responses are ignored, page/action controls select the active workflow items, frontend selection behavior has smoke tests, and frontend dependencies are pinned with Docker using `npm ci`.
- The review identified that investigation data existed only through API responses. The fix adds an explicit investigation control and a rich evidence review surface while masking sensitive values before evidence is returned for display.
- Verification identified three workflow issues, and the project owner directed the fix: investigating a received incident now moves it to `investigating` and records an investigation timeline event; action controls remain hidden until investigation is complete; and investigation/action boundaries reject scenarios whose service does not match the incident. Stale action records are also excluded from the active UI controls.
- The remaining external-boundary review identified three open edges: live model verification, provider-backed notification and ownership resolution, and reconciliation of an interrupted action. The implementation now exposes these as explicit, opt-in configuration boundaries with local fallback where safe; end-to-end provider verification remains a separate check.
- A live check initially showed an unavailable model result because the selected incident reused a persisted investigation result from an earlier unconfigured run. The investigation service now retries persisted non-completed results when a provider is configured; completed results remain idempotent.
- Test verification found that a local provider credential contaminated tests intended to exercise the unconfigured path. Those tests now remove provider variables explicitly, keeping fallback and restart-idempotency assertions deterministic.
- The project owner identified that a key-only local configuration left the model URL empty outside Compose. The fix applies the documented default provider URL in the application gateway while preserving explicit URL overrides.
- The review identified two remaining state-safety gaps: dependency-labelled alerts were not included in correlation, and human decisions had no stale-version guard. The fix adds dependency-aware grouping and optional incident-version checks for page responses and action decisions, with persisted version tokens.
- A live provider check listed available models successfully but rejected the requested model invocation with HTTP 403. The application correctly preserves the investigation evidence and returns a failed model status; the remaining correction is provider-side model permission or credential configuration.
- The fresh live investigation exposed a PostgreSQL repository row-shape mismatch after the restart-safety change. The project owner-directed fix aligned the timeline append connection with the repository's dictionary-row contract; the rebuilt Docker/Postgres suite then returned 31 passing tests.
- Found a restart-only paging bug: overdue-page recovery read database rows as tuples while indexing them as mappings. The fix uses mapping rows for the recovery transaction and keeps action recovery field-safe.

These contributions are recorded as detection, direction, and verification; implementation changes remain explicitly attributed as AI-assisted.

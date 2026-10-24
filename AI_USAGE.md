# AI Usage

## Deliberately authored work

The project is being developed as peer programming. The project owner directs and approves the design; implementation logic is AI-assisted and reviewed against that design.

- High-level architecture, low-level classes, relationships, API catalog, data model, and service boundaries.
- Baseline runtime decisions, local Compose workflow, credential handling, port allocation, and safety boundaries.
- Feature acceptance criteria, scenario expectations, runbook structure, and final review direction.

## AI-assisted implementation

- Runtime wiring, simulator scenarios, alert normalization, correlation, deduplication, persistence, investigations, model boundary, paging, actions, durable jobs, recovery, timeline APIs, frontend console, evaluation cases, and demo scripts.
- Tests, migrations, Docker wiring, local HTTP boundary adapters, evidence masking, structured response validation, retry behavior, and UI selection safeguards.

## Verification findings and human direction

The project owner identified, prioritized, or reviewed the following grouped findings during verification:

- **Build and runtime:** missing frontend type declarations, incomplete test-image contents, worker startup ordering, environment propagation, network egress, and container test permissions.
- **Workflow correctness:** duplicate delivery, correlation, stale decisions, timeline ordering, investigation state, durable jobs, paging fallback, action approval, idempotency, execution attempts, and verification recovery.
- **Model and evidence safety:** provider configuration, request format, bounded evidence, masking, citations, structured output, degraded status handling, persistence, and retry behavior.
- **UI behavior:** stable incident selection, scenario/target matching, stale response protection, active page/action selection, investigation controls, evidence review, queued states, replies, and timeline context.
- **UI interaction review:** the owner identified stale responder targeting, cluttered step labels, generic inline failures, and repeated action clicks. The UI now uses the newest page record, exposes server validation details in a dismissible toast, blocks duplicate work while queued, and gives each workflow section one clear primary action.
- **UI comprehension review:** the owner identified raw JSON overload and unclear live-demo sequencing. The UI now leads with a guided workflow, a plain-language investigation result, labeled evidence fields, readable timeline summaries, collapsed evidence/audit sections, and opt-in raw payload disclosure.
- **UI review follow-up:** the owner identified cluttered controls, missing reply availability after acknowledgement, premature action buttons during queued investigations, and scenario-selection mismatch. The frontend now groups workflow controls, derives the scenario from the selected service, keeps replies available through acknowledgement, and blocks actions until investigation completion.
- **Workflow status clarity:** the owner identified that the progress strip could mark a step complete merely because a record existed. The frontend now distinguishes ready, locked, active, and verified states so the operator always knows the next valid action.
- **Simulator flow gap caught during audit:** the owner’s clean-demo review exposed that generated simulator alerts were only stored in simulator state and did not create incidents. The simulator now emits webhook-ready payloads through the canonical alert intake path; flapping deliveries also use distinct lifecycle event identities and source ordering.
- **UI feedback issue caught during verification:** the owner identified that a repeated investigation could look frozen while the result refresh was pending, and that the three workflow areas were difficult to understand. The frontend now confirms accepted actions in a toast, releases the button without waiting for the worker refresh, and labels the workflow by user intent.
- **End-to-end demo issue caught during verification:** the owner identified that investigation, response, and action controls were visible together and that the final verification could fail after a worker completed the action. The workflow is now sequential, shows background progress, and verifies from the persisted worker result across the API/worker process boundary.
- **Assignment-flow closure issues caught during verification:** the owner identified that a completed investigation did not produce a clear terminal timeline state, verified remediation did not close the incident, reply follow-up could become inert, and an external-dependency finding could look like it needed a local action. The implementation now records investigation completion, `resolved`, and `unfixable` outcomes, keeps follow-up response controls active, and labels no-local-fix cases explicitly.
- **Delivery quality:** HLD/LLD/API alignment, golden evaluations, runbooks, repeatable demos, local Docker/PostgreSQL proof, frontend build proof, and explicit separation between verified behavior and future add-ons.
- **Frontend structure:** the owner-directed UI cleanup keeps screen orchestration, domain types, reusable selection helpers, and styles in separate folders without adding a component framework or unnecessary abstraction.
- **Realistic-investigation review:** the owner identified that generic fixture evidence and hidden model output made the result difficult to trust. The implementation now uses concrete e-commerce signals, names each bounded evidence query, persists safe telemetry, and renders the structured model readout beside the deterministic finding.
- **Final browser review:** the owner identified that repeated responder content obscured the workflow. The refreshed UI has one responder section, sequential controls, labeled evidence cards, collapsed raw details, and a visible toast when a background investigation is accepted.

These contributions are recorded as human detection, direction, and verification; implementation changes remain explicitly attributed as AI-assisted.

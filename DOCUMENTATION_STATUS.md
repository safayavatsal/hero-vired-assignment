# Documentation Status

## Current feature parity audit

| Version | Scope | Current result |
|---|---|---|
| 0.0 | Baseline, simulator, and runtime | Implemented; static checks and live readiness pass |
| 0.1 | Simulator controls and typed actions | Implemented; deterministic behavior covered by the backend suite |
| 0.2 | Alert normalization, deduplication, correlation, and timeline | Implemented; live duplicate delivery returned `duplicate: true` |
| 0.3 | Durable incident state and recovery guards | Implemented; PostgreSQL persistence and version checks are present |
| 0.4 | Evidence-first investigation and model boundary | Implemented with durable investigation jobs; fresh worker-backed live investigation completed with model analysis |
| 0.5 | Paging, replies, ownership, and escalation | Implemented; owner notes are optional before acknowledgement, acknowledgement closes the response step, and deeper investigation is explicit |
| 0.6 | Approval, durable execution, attempts, and verification | Implemented; rebuilt Docker/PostgreSQL suite passed with migrations `002_jobs.sql` and `003_action_attempts.sql` |
| 0.7 | Incident UI and selection safety | Implemented; frontend smoke tests, build, and port `8000` health pass |
| 0.8 | Resilience, security, and cost bounds | Implemented; Docker/PostgreSQL backend suite returned 37 passing tests with no warnings |
| 0.9 | Tests and deterministic evaluation | Implemented; golden cases cover all three scenarios and the Docker suite returned 45 passing tests with no warnings |
| 1.0 | Compose, documentation, and demo delivery | Implemented; clean-checkout defaults, runnable demo/reset scripts, and live-change coverage are present |
| demo commerce | Catalog-to-checkout incident proof | Implemented; synthetic approved/declined payment paths, canonical alert intake, customer-safe payment references, and captured responder email are present |
| embedded observer | Monitored-service integration boundary | Implemented; the store backend emits bounded, correlated operational events without exposing operator tooling in the customer UI |
| scenario extensibility | Data-only live scenario addition | Implemented; finding rules live in scenario definitions, the simulator scenario endpoint registers new scenarios at runtime with restart persistence, and the UI derives and reselects scenario metadata from the public listing even when it loads after incident details. Backend suite returned 55 passing tests; frontend tests (6) and production build pass |
| submission readiness | Reviewer and on-site delivery artifacts | Implemented; `DECISIONS.md` now includes the required concise trade-off and scale summary, on-site paths are mapped in decision 022 and feature 17, and malformed structured model output is rejected with focused test coverage |
| submission preflight | One-command local proof | Implemented; `scripts/verify-submission.sh` checks Compose, readiness, served frontends, the demo-store proxy, both backend test suites, frontend builds, the commerce workflow, and the working-tree diff |
| customer scenario storefront | Browser-triggered coverage of all three built-in incidents | Implemented; the store exposes slow-checkout, delayed-fulfillment, and provider-unavailable journeys, while the commerce verifier proves their bounded alert handoff |
| guided investigation workflow | Context selection and sequential operator language | Implemented; the console auto-selects the incident context, keeps controlled overrides advanced-only, explains ownership and remediation, and previews action state changes before approval |
| parity | Cross-document and executable-contract closure | Complete for the local assignment boundary; evidence provenance, page context, prompt contract, schema/API catalog, UI context, static checks, frontend build, graph refresh, and Docker/Postgres verification are aligned. Reference parity add-ons are documented separately and not implemented |
| investigation runbook catalog | Scenario-owned bounded checklist | Implemented; scenario definitions expose four explanation-first checks and the UI reflects pending, active, and completed investigation states |
| evidence tool catalog | Explicit bounded evidence contract | Implemented; enabled tools expose purpose and stable names through the API and persisted investigation traces |
| resource analyzer surface | Kubernetes resource health checks | Implemented; six read-only analyzers expose namespace, kind, name, label, and analyzer filters through the analysis API, and the console now exposes a dedicated Kubernetes health tab with a visible sample scan and finding cards; Docker suite returned 70 passing tests and browser verification completed |
| Helm local extension | Additive Kubernetes packaging | Implemented; the chart packages the API, worker, database, notification capture, incident UI, and demo store with configurable images, resources, persistence, probes, security settings, port-forward notes, and a Helm smoke-test hook |
| Similar past incidents | Bounded historical finding context | Implemented; deterministic vectors are persisted for completed findings, ranked context is exposed as a fifth bounded evidence source, retrieval failures degrade to uncertainty, and the console renders the historical finding panel |
| Bounded evidence loop | Optional model-directed evidence | Implemented; allowlisted re-queries are validated server-side, re-enter citation validation, and stop safely at round, request, item, or wall-clock limits |
| Cost and latency telemetry | Model and evidence timing readout | Implemented; bounded token estimates, finite cost, source durations, retrieval latency, and a compact evidence-panel summary are persisted and rendered |

The approved HLD and LLD remain the authority for boundaries and relationships. The current implementation includes durable investigation and action jobs, action-attempt, verification, delivery-attempt, and worker-startup pieces required by those documents.

## Baseline runtime

Status: Implemented and verified locally through the Docker/Postgres stack.

Implemented:

- FastAPI service with liveness and PostgreSQL readiness endpoints.
- React + TypeScript frontend shell.
- Python worker process.
- PostgreSQL service in Docker Compose.
- Frontend on host port `8000`.
- Backend on host port `8001`.
- Three deterministic simulator scenarios.
- Simulator evidence query, alert, typed action, reset, and verification endpoints.
- Alert webhook normalization, fingerprinting, deduplication, incident correlation, and timeline read APIs.
- PostgreSQL-backed incident, alert, and timeline persistence with versioned backend migrations applied at startup.
- Transactional alert idempotency and restart-safe incident reads.
- Validated incident state transitions with timeline events and version checks.
- Bounded deterministic investigation with evidence identifiers, findings, confidence, uncertainty, and citations.
- PostgreSQL-backed investigation, evidence, and finding records.
- Visible degraded results when an evidence source is unavailable.
- Model boundary with sensitive-value masking, structured response validation, and safe degraded statuses.
- Contradictory evidence detection and versioned investigation caching.
- Optional file-backed simulator state for local restart recovery.
- Simulator delivery ordering/delay controls and action idempotency keys.
- Restart-safe reuse of persisted investigations.
- Structured-output adapter configuration for a Responses-compatible provider.
- Persisted primary/fallback pages with acknowledgement, reply, and one-time escalation.
- Typed action proposals, human approval/rejection, idempotent execution, verification, and timeline audit events.
- Scenario and target validation before an action can be approved.
- Stable incident selection while the UI refreshes its list.
- Serialized timeline sequence allocation for concurrent workflow writes.
- Stale-response protection for rapid incident selection changes.
- Active-page and scenario/target-matched action selection in the UI instead of first-item assumptions.
- Frontend selection smoke tests and reproducible locked Docker installs.
- Investigation control and evidence review surface with findings, confidence, uncertainty, citations, source availability, timestamps, and masked payloads.
- Investigation lifecycle transition and timeline recording for received incidents.
- Backend scenario/service and investigation-state checks before action proposals.
- React incident list and timeline view with refresh and empty/error states.
- Explicit simulator responder/dependency failure controls.
- Service/time-window incident correlation beyond explicit correlation keys.
- Startup recovery for interrupted actions and overdue pages.
- Opt-in HTTP boundaries for model-backed investigation, notification delivery, service ownership lookup, and unknown-action reconciliation.
- Compose loads database and runtime credentials from `.env`; secret values are not written into `docker-compose.yml`.
- Backend and frontend use multi-stage production images; the backend runs non-root, and the frontend serves the built application through an unprivileged web server with API proxying.
- Durable jobs now persist queued, leased, succeeded, retried, and dead-lettered work with idempotency keys and lease timestamps.
- The worker claims typed action jobs, executes them through the workflow boundary, and recovers overdue pages during polling.
- Page delivery attempts are persisted, including fallback delivery records.
- Action attempts and post-action verifications are persisted separately from the action proposal.
- Worker startup waits for API migration readiness and retries transient database-startup failures.
- Feature 8 bounds evidence collection with concurrent per-source deadlines, caps model evidence and prompt size, applies configurable model and external-boundary deadlines, version-stamps investigation cache keys, and delays durable retries with capped exponential backoff.
- Feature 9 adds committed golden investigation cases with expected categories, safe next steps, confidence bounds, citation checks, required evidence sources, and prompt-version alignment.
- Feature 10 adds clean-checkout Compose defaults, repeatable all-scenario demo/reset scripts, and a focused live-change analyzer path.
- The UI refreshes the selected incident while polling, supports free-form page replies, and displays queued and running action states.
- Investigation completion, no-local-fix classification, and verified remediation are visible as explicit terminal timeline states; verified local actions resolve the incident.
- Similar-incident retrieval uses no new service or required credential, stores vectors in PostgreSQL, excludes the current incident, and leaves deterministic findings unchanged when history is empty or retrieval is unavailable.
- The optional evidence loop is enabled only for configured model gateways; missing models preserve the fixed path, while invalid requests and exhausted bounds remain telemetry rather than errors.
- Model telemetry now includes estimated prompt/completion tokens, finite non-negative cost, source durations, and similar-history retrieval latency; local rate settings are optional.

## Environment-dependent verification:

- The model gateway now applies its documented default URL when only a credential is configured. Persisted non-completed investigations retry when the provider is configured; the running container must be recreated after changing `.env` so it receives the current credential. The worker has dedicated egress for configured external model calls.
- External notification, ownership, and action-executor calls are environment-configured. Their real HTTP adapter paths are verified against a local HTTP boundary with bearer headers, bounded payloads, response validation, and fallback behavior. Hosted deployment verification is intentionally out of scope for this local test assignment.
- Provider URL and response format are read from `MODEL_GATEWAY_URL` and `MODEL_GATEWAY_FORMAT`; the worker-backed live provider path is verified with the configured environment.

## Verification record:

- `docker compose up -d --build` previously started the Compose services with healthy Postgres.
- `curl http://localhost:8001/api/v1/readiness` returned `{"status":"ready","database":"ok"}`.
- Earlier rebuilt Docker/PostgreSQL runs returned `35 passed in 19.81s` with no warnings; this includes the localhost HTTP boundary integration test. The API and worker containers remained healthy after startup.
- `npm test` returned 3 passing frontend selection checks, and `npm run build` passed.
- The evidence review change passed the same frontend build, backend test, Docker/Postgres readiness, and frontend HTTP checks.
- Live Feature 5–7 happy path persisted an acknowledged page, a verified action, and seven timeline events.
- Live timeout retry path persisted one escalated primary page and one delivered fallback page without duplication.
- Frontend health check on port `8000` returned HTTP 200.
- Boundary adapter tests cover opt-in configuration, bearer-token forwarding, response validation, and local fallback.
- The external-boundary integration test exercised real localhost HTTP requests for ownership lookup, notification delivery, and action reconciliation, including bearer headers and exact bounded payloads.
- Dependency-aware incident correlation and stale human-decision version guards are covered in the current implementation and test suite.
- Live host verification accepted the exact application-generated Responses payload with HTTP 200, and the response parser produced all required structured fields. A fresh worker-backed investigation after the egress fix completed with `model_status=completed`, model analysis present, one finding, and four evidence groups.
- The restart recovery audit found and fixed overdue-page row handling before the final handoff.
- The current parity pass adds migration `003_action_attempts.sql`; the migration and separate attempt/verification records are covered by the rebuilt Docker/PostgreSQL suite.
- A fresh live investigation request returned a queued response, and the worker completed it against PostgreSQL with persisted model analysis, one finding, and four evidence groups after the worker environment and egress wiring were corrected.
- Earlier rebuilt Docker/PostgreSQL runs returned `37 passed in 20.00s` and the Feature 9 run returned `39 passed`, with no warnings; these include slow-evidence degradation, configurable external-boundary timeout coverage, and golden evaluation cases.
- The current backend suite contains 45 tests; the frontend smoke suite contains 5 tests and the production build passes.
- Feature 10 verification includes Compose config validation, the full Docker backend suite, frontend tests/build, and documentation checks. The demo scripts are ready for local runtime execution after `docker compose up --build`.
- Latest flow-parity verification rebuilt the API image and returned `47 passed in 24.82s` with no pytest warnings; simulator deliveries now enter incident intake directly.
- The parity closure verification added page context to delivery, refreshed the code graph, passed the restricted-reference scan, and completed the frontend build plus a 40-test Docker/Postgres suite.
- Final delivery verification recreated the Docker stack, passed the 41-test backend suite, passed frontend tests and the production build, returned healthy liveness/readiness responses, served the UI on port `8000`, and completed a fresh worker-backed model investigation with persisted structured analysis.
- The repeatable demo was executed against the running Compose stack on 2026-10-23. All three scenarios produced duplicate, late, flapping, delayed, and out-of-order deliveries; the dependency failure-mode check returned `availability: unavailable`.
- The frontend production build passes, and interactive browser verification on port `8000` confirmed the rebuilt UI renders the selected incident, guided workflow, readable finding, collapsed evidence/audit sections, responder state, action state, timeline summaries, and opt-in raw payload disclosures.
- The frontend workflow review covers scenario auto-selection, sequential investigation/response/action gating, visible background progress, responder reply state, duplicate-click prevention, grouped controls, responsive layout, keyboard focus states, and toast error handling. The selected incident remains the source of truth for all controls.
- The latest live browser walkthrough created a fresh disk-pressure incident and completed the UI path through investigation, finding, page, acknowledgement, proposal, approval, queue, worker completion, and service verification. The process-boundary verification defect was fixed by using the persisted worker result when the API-local simulator cannot see the worker-local action.
- The follow-up browser walkthrough confirmed the same path with revised labels for investigation context, owner notification and acknowledgement, remediation approval, queueing, completion, and service verification.
- The latest UI pass removes decorative step labels, keeps workflow controls grouped, fixes newest-page selection after acknowledgement, confirms accepted actions in a success toast without waiting for a worker refresh, and displays action failures as an auto-clearing toast with server detail. Frontend tests, production build, diff checks, taste lint, the rebuilt Docker/PostgreSQL suite (`42 passed in 19.31s`), and live browser rendering pass.
- The frontend workflow strip now derives each step from its actual state: response is locked before a finding, action is locked before acknowledgement, and completion is reserved for a verified action. Five frontend smoke tests and the production build pass after this change.
- Simulator-triggered alert deliveries now flow through canonical incident intake, and lifecycle state follows the newest source event for out-of-order delivery handling.
- A local OrbStack Kubernetes manifest now mirrors the Compose services with `imagePullPolicy: Never`, in-cluster API proxying, readiness probes, and port-forward instructions for the same host ports.
- OrbStack Kubernetes verification passed after adding database startup gates and an explicit worker command: API, worker, database, and frontend rolled out with zero restarts; readiness returned `{"status":"ready","database":"ok"}`; two repeated worker-backed investigations completed with one finding and four evidence groups each.
- The Kubernetes browser pass completed the guided incident workflow end to end: investigation, responder page, acknowledgement, reply, action proposal, approval, queueing, worker completion, and service verification. The in-cluster API suite returned `42 passed` with pytest cache collection disabled to avoid non-root cache warnings.
- Docker/PostgreSQL verification was repeated twice after the Kubernetes changes; both runs returned `42 passed` with no pytest warning output. Frontend smoke tests returned 4 passing tests and the production build passed.
- Browser-only Kubernetes demo recordings were created under `demo-output/` and checked as valid QuickTime/H.264 files; the workflow recording includes live investigation feedback.
- The realistic-investigation quality plan completed on 2026-10-24: Docker/PostgreSQL returned 49 passing tests with no warnings, frontend smoke tests and production build passed, Compose validation passed, the restricted-reference scan was empty, and browser verification confirmed the refreshed guided UI, model readout, labeled evidence, and investigation toast.
- The commerce demo adds separate frontend and backend projects on ports `8003` and `8004`, plus the captured inbox on port `8002`. Seven store-backend tests prove approved and declined routing, input validation, endpoint behavior, credential exclusion, and an unchanged declined outcome when observer delivery is unavailable. The customer storefront exposes payment references only; an embedded observer emits the canonical operational event separately. The main backend has 50 sandbox-compatible passing tests, the main frontend has five passing workflow tests, both production frontend builds pass, Compose validates, and the local Kubernetes manifest parses. On 2026-10-25, the Compose smoke verifier completed an approved payment, a declined payment with a fresh incident, investigation completion, page delivery, and one captured inbox message. The live browser pass repeated the declined checkout, fresh incident, completed investigation, responder page, captured notification, and an approved checkout with no new incident.
- The investigation review surface now presents a structured brief, model status/latency, bounded tool trace, query timing, source availability, parameters, and opt-in raw payloads. The frontend smoke suite, production build, diff checks, and full local submission verifier pass after this change.
- Helm extension verification passed `helm lint`, default and credential-override `helm template`, chart packaging, packaged test-hook presence, resource rendering, and `git diff --check`. Live Helm install and `helm test` remain pending until the local Kubernetes API is running; the attempted install reported `127.0.0.1:26443 connection refused`.
- Similar-incident verification passed the focused ranking, empty-history, and failure-isolation tests, the backend suite (`73 passed`), frontend tests (`6 passed`), and the production build. Live Compose proof is pending because the local container runtime is not running.
- Bounded-loop verification passed allowlist, citation revalidation, round-cap, and no-model-path tests; the prompt contract hash and golden evaluation contract remain unchanged.
- Telemetry verification passed sane token/cost/source-latency assertions, the full backend suite (`77 passed`), frontend tests (`6 passed`), and the production build.
- Scenario onboarding verification covers local definition validation, one registration request, one alert request, incident-id extraction, and the one-page presenter guide; the stub-server test is the automated proof.
- On 2026-10-26, the rebuilt Compose stack passed config/readiness checks, the complete commerce verifier covered approved checkout, controlled decline, slow checkout, and delayed fulfillment, and two fresh disk-pressure investigations surfaced the first finding as ranked similar history without changing the deterministic finding. The local browser confirmed the console telemetry and similar-history panel plus all three store journeys. The configured model gateway returned HTTP 400, so this live run verified deterministic degradation rather than successful model enrichment.
- On 2026-10-26, the HLD and LLD architecture diagrams were updated for historical retrieval, persisted finding embeddings, bounded evidence re-queries, and investigation telemetry. The architecture artifact passed all nine showcase validation checks and was regenerated with local source evidence.
- Queue reliability verification added persisted lease/completion timing, aggregate queue metrics at `GET /api/v1/jobs/metrics`, idempotent enqueue coverage, expired-lease recovery coverage, and a Compose backend run with 83 passing tests.

# Project-local content restrictions

These rules apply only to this repository root and everything below it.

## Restricted references

Until this rule is removed or changed, do not mention the following products or their equivalents in:

- Any document under `_research_refs/`, `_plan_docs/`, or `_decision_docs/`, including subfolders.
- Git commit messages for this project.
- Source-code comments, configuration comments, or documentation comments in this project.

Restricted references include the private external products and implementation references discussed during research, plus any named external product, project, or implementation reference that would reveal or prescribe what this assignment is being implemented with.

Keep those documents and comments focused on requirements, decisions, plans, and implementation-neutral behavior.

## Unsetting this rule

To unset or change this rule, edit or remove this `AGENTS.md` file. The rule is intentionally repository-local and does not apply outside this checkout.

## Project working agreement

- Treat the documented product direction, feature scope, HLD, LLD, classes, methods, variables, API boundaries, data model, and safety decisions as deliberately authored and approved by the project owner.
- Treat implementation logic, integrations, tests, and runtime wiring as AI-assisted work that must be reviewed and verified against the approved documents.
- Work feature by feature from `_plan_docs/_features_docs/` (00–17).
- Before each feature, inspect its related HLD, LLD, API, and decision documents.
- After each feature, update the relevant plans and the project records: `AI_USAGE.md`, `DEMO_GUIDE.md`, `DOCUMENTATION_STATUS.md`, `SCENARIO_RUNBOOK.md`, and decision records when needed.
- Perform a private parity check against supplied reference material before a feature is pushed. Keep that check internal and do not expose the references in project artifacts.
- Use the smallest complete implementation. Add comments only when they explain a non-obvious reason.
- Before committing, provide an implemented, verified, and open summary in simple language, followed by only the required Git commands.
- Use host port `8000` for the frontend and host port `8001` for the backend. Allocate later host ports sequentially.

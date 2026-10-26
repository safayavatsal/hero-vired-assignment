# Implementation Handoff

```text
Keep the repository root for documents, scripts, Compose, and demos. Group the primary product under `main-app/backend/` and `main-app/frontend/`. Keep the separate demo store and demo observability surfaces. On a failed synthetic payment or a registered scenario, send a minimal alert through the existing alert endpoint. Never place cardholder, card number, security code, address, or email data in an alert. Reuse the existing incident, fixed four-tool investigation, similar-history retrieval, bounded model evidence loop, telemetry, paging, typed remediation, verification, and explicit closure paths. Add focused tests, local captured notification behavior, browser verification, HLD/LLD updates, the architecture source and rendered diagram, and project-record updates. Do not add another database, telemetry store, vector service, or workflow engine.
```

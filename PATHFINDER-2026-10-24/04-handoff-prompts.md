# Implementation Handoff

```text
Add a separate demo store with independent frontend and backend folders. Implement a small catalog and synthetic checkout. On a declined synthetic payment, have the store backend POST a minimal alert to the existing alert endpoint. Never place cardholder, card number, security code, address, or email data in that alert. Reuse the existing incident, investigation, paging, and action paths. Add focused tests, a local captured-email notification path, Compose and local Kubernetes wiring, browser verification, and project-record updates. Do not add another database or workflow engine.
```

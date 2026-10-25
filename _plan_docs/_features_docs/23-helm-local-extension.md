# Helm Local Extension

## Goal

Make the existing local product deployable through Helm as an additive Kubernetes workflow without changing the assignment’s Docker Compose or raw-manifest behavior.

## Scope

1. Package the API, worker, PostgreSQL database, notification capture service, incident frontend, demo-store backend, and demo-store frontend.
2. Preserve the internal service names required by the existing application images.
3. Expose image tags, replicas, resources, persistence, model settings, notification settings, and database credentials through values.
4. Add readiness probes, non-root application security settings, bounded temporary storage, and a Helm smoke-test hook.
5. Document install, rollout, port-forward, and local verification commands.

## Acceptance checks

- `helm lint k8s/helm/hero-vired` passes.
- `helm template` renders all runtime services without unresolved values.
- The chart has no default model or notification credentials.
- The default local database path does not require a committed password.
- Compose and `k8s/local.yaml` remain unchanged as working alternatives.
- A local Kubernetes install can expose the incident UI on host port `8000`, API on `8001`, captured notifications on `8002`, and the demo store on `8003`/`8004` through port-forwarding.

## Status

Implemented as a local chart. Offline chart validation and packaging pass; live install remains environment-dependent on the local Kubernetes API being enabled.

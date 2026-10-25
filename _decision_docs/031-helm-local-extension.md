# Helm Local Extension

## Decision

Package the existing local runtime as a Helm chart under `k8s/helm/hero-vired` while preserving Docker Compose and the existing raw Kubernetes manifest as supported workflows.

## Why

- Keeps the assignment’s local deployment reproducible on a Kubernetes-enabled developer machine.
- Deploys the same API, worker, database, notification capture, incident UI, and demo store used by the Compose flow.
- Makes image tags, replica counts, resource bounds, persistence, model settings, and notification settings overridable.
- Keeps service names stable so the bundled proxy configuration continues to work inside the cluster.
- Provides a Helm test hook and operator notes for rollout and port-forward verification.

## Consequences

- The default chart is local-first and uses locally built images with `imagePullPolicy: Never`.
- A database password is not embedded by default; local empty-password installation uses PostgreSQL trust authentication, while shared environments must provide a password override.
- Hosted registry, ingress, authentication, and multi-tenant concerns remain outside this local extension.
- Compose and `k8s/local.yaml` remain available as independent verification paths.

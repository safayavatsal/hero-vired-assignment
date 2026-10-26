#!/usr/bin/env bash
set -euo pipefail

docker compose config -q
curl --fail-with-body -sS --max-time 5 http://localhost:8001/api/v1/readiness >/dev/null
curl --fail-with-body -sS --max-time 5 http://localhost:8000/ >/dev/null
curl --fail-with-body -sS --max-time 5 http://localhost:8003/ >/dev/null
curl --fail-with-body -sS --max-time 5 http://localhost:8003/api/store/health >/dev/null
curl --fail-with-body -sS --max-time 5 http://localhost:8004/api/store/health >/dev/null
curl --fail-with-body -sS --max-time 5 http://localhost:8005/ >/dev/null
curl --fail-with-body -sS --max-time 5 http://localhost:8006/api/observability/health >/dev/null
docker compose run --rm --user root --volume "$PWD/scripts:/scripts:ro" api pytest -q tests
docker compose run --rm --user root store-backend pytest -q tests
(cd frontend && npm test && npm run build)
(cd demo-store/frontend && npm run build)
(cd demo-observability/frontend && npm test && npm run build)
docker compose run --rm demo-observability-backend pytest -q tests
./scripts/verify-commerce-demo.sh >/dev/null
git diff --check
printf 'submission verification passed\n'

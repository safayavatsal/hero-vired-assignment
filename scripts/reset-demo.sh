#!/usr/bin/env bash
set -euo pipefail

BASE_URL="${BASE_URL:-http://localhost:8001}"
curl --fail-with-body -sS -X POST "$BASE_URL/api/v1/simulator/scenarios" \
  -H 'content-type: application/json' \
  -d '{"scenario_id":"deployment_regression"}' >/dev/null
curl --fail-with-body -sS -X POST "$BASE_URL/api/v1/simulator/reset"
printf '\nDemo state reset.\n'

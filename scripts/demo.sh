#!/usr/bin/env bash
set -euo pipefail

BASE_URL="${BASE_URL:-http://localhost:8001}"
curl --fail-with-body -sS "$BASE_URL/api/v1/readiness" >/dev/null

for scenario in deployment_regression disk_pressure third_party_outage; do
  curl --fail-with-body -sS -X POST "$BASE_URL/api/v1/simulator/scenarios" \
    -H 'content-type: application/json' \
    -d "{\"scenario_id\":\"$scenario\"}" >/dev/null
  curl --fail-with-body -sS -X POST "$BASE_URL/api/v1/simulator/alerts" \
    -H 'content-type: application/json' \
    -d "{\"scenario_id\":\"$scenario\",\"duplicate_count\":2,\"late\":true,\"flapping\":true,\"out_of_order\":true,\"delayed_seconds\":1}" \
    | sed "1s/^/$scenario: /"
done

curl --fail-with-body -sS -X POST "$BASE_URL/api/v1/simulator/scenarios" \
  -H 'content-type: application/json' \
  -d '{"scenario_id":"third_party_outage"}' >/dev/null
printf 'failure-mode evidence: '
curl --fail-with-body -sS "$BASE_URL/api/v1/simulator/evidence?source_type=service_health"
printf '\n'

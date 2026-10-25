#!/usr/bin/env bash
set -euo pipefail

STORE_URL="${STORE_URL:-http://localhost:8004}"
ASSISTANT_URL="${ASSISTANT_URL:-http://localhost:8001}"
INBOX_URL="${INBOX_URL:-http://localhost:8002}"
ATTEMPT_ID="demo-$(date +%s)"

request() {
  curl -sS --fail-with-body --max-time 10 "$@"
}

json_value() {
  python3 -c "import json,sys; value=json.load(sys.stdin); print($1)"
}

request "$STORE_URL/api/store/health" >/dev/null
request "$ASSISTANT_URL/api/v1/readiness" >/dev/null

approved=$(request -X POST "$STORE_URL/api/store/payments" \
  -H 'content-type: application/json' \
  -d "{\"attempt_id\":\"$ATTEMPT_ID-approved\",\"product_ids\":[\"desk-lamp\"],\"cardholder\":\"Demo Shopper\",\"card_number\":\"4242424242424242\",\"expiry\":\"12/30\",\"security_code\":\"123\"}")
approved_status=$(printf '%s' "$approved" | json_value 'value["status"]')
test "$approved_status" = "approved"

before=$(request "$INBOX_URL/api/v1/messages" | json_value 'len(value.get("messages", []))')
declined=$(request -X POST "$STORE_URL/api/store/payments" \
  -H 'content-type: application/json' \
  -d "{\"attempt_id\":\"$ATTEMPT_ID-declined\",\"product_ids\":[\"desk-lamp\"],\"cardholder\":\"Demo Shopper\",\"card_number\":\"4111111111110002\",\"expiry\":\"12/30\",\"security_code\":\"123\"}")
incident_id=$(printf '%s' "$declined" | json_value 'value["incident_id"]')
incident=$(request "$ASSISTANT_URL/api/v1/incidents/$incident_id")
incident_alert_count=$(printf '%s' "$incident" | json_value 'value["alert_count"]')
test "$incident_alert_count" = "1"

request -X POST "$ASSISTANT_URL/api/v1/incidents/$incident_id/investigate" \
  -H 'content-type: application/json' \
  -d '{"scenario_id":"third_party_outage"}' >/dev/null

investigation_status=""
for _ in {1..30}; do
  investigation=$(request "$ASSISTANT_URL/api/v1/incidents/$incident_id/evidence" 2>/dev/null || true)
  investigation_status=$(printf '%s' "$investigation" | python3 -c 'import json,sys; print(json.load(sys.stdin).get("status", ""))' 2>/dev/null || true)
  test "$investigation_status" = "completed" && break
  sleep 1
done
test "$investigation_status" = "completed"

page=$(request -X POST "$ASSISTANT_URL/api/v1/incidents/$incident_id/page" \
  -H 'content-type: application/json' \
  -d '{"responder":"primary-oncall","fallback_responder":"secondary-oncall","deadline_seconds":300}')
page_status=$(printf '%s' "$page" | json_value 'value["page"]["status"]')
test "$page_status" = "delivered"

after="$before"
for _ in {1..10}; do
  after=$(request "$INBOX_URL/api/v1/messages" | json_value 'len(value.get("messages", []))')
  test "$after" -gt "$before" && break
  sleep 1
done
test "$after" -gt "$before"

deployment=$(request -X POST "$STORE_URL/api/store/scenarios/deployment_regression" \
  -H 'content-type: application/json' \
  -d "{\"attempt_id\":\"$ATTEMPT_ID-deployment\",\"product_ids\":[\"desk-lamp\"]}")
deployment_status=$(printf '%s' "$deployment" | json_value 'value["status"]')
deployment_incident_id=$(printf '%s' "$deployment" | json_value 'value["incident_id"]')
test "$deployment_status" = "degraded"
test -n "$deployment_incident_id"

disk=$(request -X POST "$STORE_URL/api/store/scenarios/disk_pressure" \
  -H 'content-type: application/json' \
  -d "{\"attempt_id\":\"$ATTEMPT_ID-disk\",\"product_ids\":[\"desk-lamp\"]}")
disk_status=$(printf '%s' "$disk" | json_value 'value["status"]')
disk_incident_id=$(printf '%s' "$disk" | json_value 'value["incident_id"]')
test "$disk_status" = "delayed"
test -n "$disk_incident_id"

python3 - "$incident_id" "$approved_status" "$incident_alert_count" "$investigation_status" "$page_status" "$after" "$deployment_incident_id" "$disk_incident_id" <<'PY'
import json
import sys

print(json.dumps({
    "approved_payment": sys.argv[2],
    "declined_incident_id": sys.argv[1],
    "incident_alert_count": int(sys.argv[3]),
    "investigation": sys.argv[4],
    "page": sys.argv[5],
    "captured_messages": int(sys.argv[6]),
    "deployment_regression_incident_id": sys.argv[7],
    "disk_pressure_incident_id": sys.argv[8],
}, separators=(",", ":")))
PY

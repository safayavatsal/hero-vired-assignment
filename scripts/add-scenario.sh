#!/usr/bin/env bash
set -euo pipefail

if [[ $# -ne 1 ]]; then
  printf 'usage: %s <definition.json>\n' "$0" >&2
  exit 2
fi

definition_file=$1
if [[ ! -f "$definition_file" ]]; then
  printf 'scenario definition not found: %s\n' "$definition_file" >&2
  exit 2
fi

BASE_URL="${BASE_URL:-http://localhost:8001}"
REQUEST_TIMEOUT_SECONDS="${REQUEST_TIMEOUT_SECONDS:-10}"

post_json() {
  python3 - "$1" "$2" "$REQUEST_TIMEOUT_SECONDS" <<'PY'
import sys
import urllib.error
import urllib.request

url, payload, timeout = sys.argv[1], sys.argv[2], float(sys.argv[3])
request = urllib.request.Request(
    url,
    data=payload.encode("utf-8"),
    headers={"content-type": "application/json"},
    method="POST",
)
try:
    with urllib.request.urlopen(request, timeout=timeout) as response:
        sys.stdout.buffer.write(response.read())
except urllib.error.HTTPError as error:
    sys.stderr.buffer.write(error.read())
    raise SystemExit(1)
PY
}

mapfile -t scenario_payload < <(python3 - "$definition_file" <<'PY'
import json
import math
import re
import sys

path = sys.argv[1]
try:
    with open(path, encoding="utf-8") as handle:
        payload = json.load(handle)
except (OSError, json.JSONDecodeError) as error:
    raise SystemExit(f"invalid scenario JSON: {error}")

if not isinstance(payload, dict):
    raise SystemExit("scenario definition must be a JSON object")

scenario_id = payload.get("scenario_id") or payload.get("id")
definition = payload.get("definition", payload)
if "definition" not in payload:
    definition = dict(definition)
    definition.pop("scenario_id", None)
    definition.pop("id", None)

if not isinstance(scenario_id, str) or not re.fullmatch(r"[a-z0-9][a-z0-9_-]*", scenario_id):
    raise SystemExit("scenario_id must use lowercase letters, numbers, hyphens, or underscores")
if not isinstance(definition, dict):
    raise SystemExit("definition must be a JSON object")

for field in ("name", "service", "severity", "alert_type", "evidence", "finding"):
    if not definition.get(field):
        raise SystemExit(f"scenario definition requires {field}")
if not isinstance(definition["evidence"], dict) or not definition["evidence"]:
    raise SystemExit("scenario evidence must be a non-empty object")
if any(not isinstance(items, list) for items in definition["evidence"].values()):
    raise SystemExit("scenario evidence values must be arrays")

finding = definition["finding"]
if not isinstance(finding, dict):
    raise SystemExit("scenario finding must be an object")
for field in ("metric", "category", "statement", "suggested_next_step"):
    if not isinstance(finding.get(field), str) or not finding[field]:
        raise SystemExit(f"scenario finding requires {field}")
confidence = finding.get("confidence")
if isinstance(confidence, bool) or not isinstance(confidence, (int, float)) or not math.isfinite(confidence) or not 0 <= confidence <= 1:
    raise SystemExit("scenario finding confidence must be a finite number between 0 and 1")

if "allowed_actions" in definition and not isinstance(definition["allowed_actions"], list):
    raise SystemExit("allowed_actions must be an array")
if "allowed_actions" in definition and any(not isinstance(action, str) for action in definition["allowed_actions"]):
    raise SystemExit("allowed_actions entries must be strings")
if "initial_state" in definition and not isinstance(definition["initial_state"], dict):
    raise SystemExit("initial_state must be an object")
if "controls" in definition and not isinstance(definition["controls"], dict):
    raise SystemExit("controls must be an object")
runbook = definition.get("runbook", [])
if not isinstance(runbook, list) or any(
    not isinstance(step, dict) or not all(isinstance(step.get(field), str) and step[field].strip() for field in ("id", "title", "purpose"))
    for step in runbook
):
    raise SystemExit("scenario runbook steps require id, title, and purpose")

print(scenario_id)
print(json.dumps(definition, separators=(",", ":")))
PY
)

scenario_id=${scenario_payload[0]}
definition_json=${scenario_payload[1]}
registration_payload=$(python3 - "$scenario_id" "$definition_json" <<'PY'
import json
import sys

print(json.dumps({"scenario_id": sys.argv[1], "definition": json.loads(sys.argv[2])}, separators=(",", ":")))
PY
)

post_json "$BASE_URL/api/v1/simulator/scenarios" "$registration_payload" >/dev/null

alert_payload=$(python3 - "$scenario_id" <<'PY'
import json
import sys

print(json.dumps({"scenario_id": sys.argv[1]}, separators=(",", ":")))
PY
)
alert_response=$(post_json "$BASE_URL/api/v1/simulator/alerts" "$alert_payload")

python3 - "$alert_response" <<'PY'
import json
import sys

try:
    response = json.loads(sys.argv[1])
    accepted = response.get("accepted")
    incident_id = accepted[0]["incident"]["id"]
except (AttributeError, IndexError, KeyError, TypeError, json.JSONDecodeError) as error:
    raise SystemExit(f"alert response did not contain an incident id: {error}")

print(incident_id)
PY

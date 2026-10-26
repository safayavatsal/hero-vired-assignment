# Scenario onboarding

Use `scripts/add-scenario.sh` to register one new scenario and create its first incident.

## 1. Write the definition

Create a JSON file with a lowercase `scenario_id` and a `definition` object:

```json
{
  "scenario_id": "queue_backlog",
  "definition": {
    "name": "Queue backlog",
    "service": "orders-worker",
    "severity": "high",
    "alert_type": "queue_depth_high",
    "evidence": {
      "metrics": [{"name": "queue_depth", "value": 90, "threshold": 50}]
    },
    "finding": {
      "metric": "queue_depth",
      "category": "queue_backlog",
      "statement": "Queue depth is above threshold.",
      "confidence": 0.9,
      "suggested_next_step": "scale"
    }
  }
}
```

The definition requires `name`, `service`, `severity`, `alert_type`, a non-empty `evidence` object, and a `finding` with `metric`, `category`, `statement`, `confidence`, and `suggested_next_step`. Optional fields include `hidden_cause`, `allowed_actions`, `initial_state`, `controls`, and `runbook`.

## 2. Register and trigger

Start the local stack, then run:

```bash
./scripts/add-scenario.sh queue-backlog.json
```

The command validates the JSON, registers it at the simulator API, sends one alert, and prints the created incident ID. Set `BASE_URL` when the backend is not on its default port:

```bash
BASE_URL=http://localhost:8001 ./scripts/add-scenario.sh queue-backlog.json
```

## 3. Investigate

Open `http://localhost:8000`, select the printed incident, and start its investigation. The console gets the new service, finding rule, allowed actions, and runbook from the scenario listing. Invalid definitions are rejected before registration; built-in scenarios cannot be replaced.

The script does not send credentials or require an external service. It needs only the running backend, `curl`, and Python 3.

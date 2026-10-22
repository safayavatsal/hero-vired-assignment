import json
import os
from dataclasses import asdict, dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Any
from uuid import UUID, uuid4


@dataclass(frozen=True)
class ScenarioDefinition:
    id: str
    name: str
    service: str
    severity: str
    alert_type: str
    hidden_cause: str
    evidence: dict[str, list[dict[str, Any]]]
    allowed_actions: tuple[str, ...]
    controls: dict[str, Any]
    initial_state: dict[str, Any]


@dataclass
class SimulatorState:
    scenario_id: str | None = None
    alerts: list[dict[str, Any]] = field(default_factory=list)
    actions: list[dict[str, Any]] = field(default_factory=list)
    service_state: dict[str, Any] = field(default_factory=dict)


def scenario_definitions() -> dict[str, ScenarioDefinition]:
    return {
        "deployment_regression": ScenarioDefinition(
            id="deployment_regression",
            name="Deployment regression",
            service="payments-api",
            severity="critical",
            alert_type="p99_latency_high",
            hidden_cause="release-2026.10.22 introduced a slow payment query",
            evidence={
                "logs": [{"message": "payment query exceeded 3 seconds", "level": "error"}],
                "metrics": [{"name": "p99_latency_ms", "value": 3210, "threshold": 2000}],
                "deploys": [{"version": "2026.10.22", "previous_version": "2026.10.21"}],
                "service_health": [{"service": "payments-api", "healthy": False}],
            },
            allowed_actions=("rollback", "restart"),
            controls={
                "evidence_slow": ["logs"],
                "action_timeout_after_completion": ["rollback"],
                "responder_non_response": False,
                "third_party_outage": False,
            },
            initial_state={"version": "2026.10.22", "healthy": False, "p99_latency_ms": 3210},
        ),
        "disk_pressure": ScenarioDefinition(
            id="disk_pressure",
            name="Disk pressure",
            service="orders-worker",
            severity="high",
            alert_type="disk_usage_high",
            hidden_cause="worker artifacts were not cleaned after repeated jobs",
            evidence={
                "logs": [{"message": "artifact cleanup skipped", "level": "warn"}],
                "metrics": [{"name": "disk_usage_percent", "value": 96, "threshold": 85}],
                "deploys": [{"version": "2026.10.20", "previous_version": "2026.10.19"}],
                "service_health": [{"service": "orders-worker", "healthy": True}],
            },
            allowed_actions=("clear_disk", "restart", "scale"),
            controls={
                "evidence_slow": [],
                "action_timeout_after_completion": [],
                "responder_non_response": True,
                "third_party_outage": False,
            },
            initial_state={"disk_usage_percent": 96, "replicas": 1, "healthy": True},
        ),
        "third_party_outage": ScenarioDefinition(
            id="third_party_outage",
            name="Third-party outage",
            service="checkout-api",
            severity="high",
            alert_type="dependency_errors_high",
            hidden_cause="external payment provider is unavailable",
            evidence={
                "logs": [{"message": "upstream provider returned 503", "level": "error"}],
                "metrics": [{"name": "provider_error_rate", "value": 100, "threshold": 5}],
                "deploys": [{"version": "2026.10.18", "previous_version": "2026.10.17"}],
                "service_health": [{"service": "checkout-api", "healthy": True}],
            },
            allowed_actions=(),
            controls={
                "evidence_slow": [],
                "action_timeout_after_completion": [],
                "responder_non_response": False,
                "third_party_outage": True,
            },
            initial_state={"provider_available": False, "healthy": True},
        ),
    }


class SimulatorService:
    def __init__(self, state_path: str | None = None) -> None:
        self._definitions = scenario_definitions()
        self._state_path = state_path or os.getenv("SIMULATOR_STATE_PATH")
        self._state = self._load()

    def list_scenarios(self) -> list[dict[str, Any]]:
        return [self._public_definition(definition) for definition in self._definitions.values()]

    def select_scenario(self, scenario_id: str) -> dict[str, Any]:
        definition = self._definition(scenario_id)
        self._state = SimulatorState(
            scenario_id=scenario_id,
            service_state=dict(definition.initial_state),
        )
        self._save()
        return self.state()

    def reset(self) -> dict[str, Any]:
        scenario_id = self._state.scenario_id
        definition = self._definition(scenario_id) if scenario_id else None
        self._state = SimulatorState(
            scenario_id=scenario_id,
            service_state=dict(definition.initial_state) if definition else {},
        )
        self._save()
        return self.state()

    def state(self) -> dict[str, Any]:
        definition = self._definition(self._state.scenario_id) if self._state.scenario_id else None
        return {
            "scenario": self._public_definition(definition) if definition else None,
            "alert_count": len(self._state.alerts),
            "action_count": len(self._state.actions),
            "service_state": self._state.service_state,
            "actions": self._state.actions,
        }

    def trigger_alert(
        self,
        scenario_id: str | None,
        duplicate_count: int,
        late: bool,
        flapping: bool,
        out_of_order: bool = False,
        delayed_seconds: int = 0,
    ) -> dict[str, Any]:
        selected_id = scenario_id or self._state.scenario_id
        definition = self._definition(selected_id)
        if duplicate_count < 1 or duplicate_count > 5:
            raise ValueError("duplicate_count must be between 1 and 5")

        source_event_id = str(uuid4())
        source_time = datetime.now(timezone.utc)
        if late:
            source_time -= timedelta(hours=1)
        lifecycles = ["firing", "resolved"] if flapping else ["firing"]
        deliveries = []
        for lifecycle in lifecycles:
            for delivery_index in range(duplicate_count):
                alert = {
                    "id": str(uuid4()),
                    "source_event_id": source_event_id,
                    "delivery_index": delivery_index,
                    "scenario_id": definition.id,
                    "service": definition.service,
                    "severity": definition.severity,
                    "alert_type": definition.alert_type,
                    "lifecycle": lifecycle,
                    "source_time": source_time.isoformat(),
                    "received_time": (datetime.now(timezone.utc) + timedelta(seconds=delayed_seconds)).isoformat(),
                }
                self._state.alerts.append(alert)
                deliveries.append(alert)
        if out_of_order:
            deliveries.reverse()
        self._save()
        return {"scenario_id": definition.id, "deliveries": deliveries}

    def query_evidence(self, source_type: str) -> dict[str, Any]:
        definition = self._require_selected()
        if source_type not in definition.evidence:
            raise ValueError("unsupported evidence source")
        availability = "slow" if source_type in definition.controls["evidence_slow"] else "available"
        return {
            "scenario_id": definition.id,
            "source_type": source_type,
            "availability": availability,
            "observed_at": datetime.now(timezone.utc).isoformat(),
            "items": definition.evidence[source_type],
        }

    def execute_action(
        self,
        action_type: str,
        target: str,
        parameters: dict[str, Any],
        idempotency_key: str | None = None,
    ) -> dict[str, Any]:
        definition = self._require_selected()
        if action_type not in definition.allowed_actions:
            raise ValueError("action is not allowed for the selected scenario")
        if idempotency_key:
            for action in self._state.actions:
                if action.get("idempotency_key") == idempotency_key:
                    return action
        now = datetime.now(timezone.utc).isoformat()
        timed_out = action_type in definition.controls["action_timeout_after_completion"]
        state_before = dict(self._state.service_state)
        state_after = self._apply_action(action_type, parameters)
        record = {
            "id": str(uuid4()),
            "scenario_id": definition.id,
            "action_type": action_type,
            "target": target,
            "parameters": parameters,
            "status": "timed_out" if timed_out else "completed",
            "requested_at": now,
            "started_at": now,
            "completed_at": now,
            "state_before": state_before,
            "state_after": state_after,
            "verified": False,
            "idempotency_key": idempotency_key,
        }
        self._state.actions.append(record)
        self._save()
        return record

    def verify_action(self, action_id: UUID) -> dict[str, Any]:
        for action in self._state.actions:
            if action["id"] == str(action_id):
                action["verified"] = True
                action["verified_at"] = datetime.now(timezone.utc).isoformat()
                self._save()
                return action
        raise ValueError("action not found")

    def _apply_action(self, action_type: str, parameters: dict[str, Any]) -> dict[str, Any]:
        state = dict(self._state.service_state)
        if action_type == "rollback":
            state["version"] = "2026.10.21"
            state["healthy"] = True
            state["p99_latency_ms"] = 850
        elif action_type == "clear_disk":
            state["disk_usage_percent"] = 62
        elif action_type == "restart":
            state["restarts"] = state.get("restarts", 0) + 1
        elif action_type == "scale":
            replicas = parameters.get("replicas")
            if not isinstance(replicas, int) or replicas < 1:
                raise ValueError("scale requires a positive integer replicas parameter")
            state["replicas"] = replicas
        self._state.service_state = state
        return state

    def _require_selected(self) -> ScenarioDefinition:
        if not self._state.scenario_id:
            raise ValueError("select a scenario first")
        return self._definition(self._state.scenario_id)

    def _load(self) -> SimulatorState:
        if not self._state_path:
            return SimulatorState()
        try:
            with open(self._state_path, encoding="utf-8") as handle:
                payload = json.load(handle)
            return SimulatorState(
                scenario_id=payload.get("scenario_id"),
                alerts=payload.get("alerts", []),
                actions=payload.get("actions", []),
                service_state=payload.get("service_state", {}),
            )
        except (FileNotFoundError, json.JSONDecodeError, OSError):
            return SimulatorState()

    def _save(self) -> None:
        if not self._state_path:
            return
        directory = os.path.dirname(self._state_path)
        if directory:
            os.makedirs(directory, exist_ok=True)
        temporary_path = f"{self._state_path}.tmp"
        with open(temporary_path, "w", encoding="utf-8") as handle:
            json.dump(asdict(self._state), handle)
        os.replace(temporary_path, self._state_path)

    def _definition(self, scenario_id: str | None) -> ScenarioDefinition:
        if not scenario_id or scenario_id not in self._definitions:
            raise ValueError("unknown scenario")
        return self._definitions[scenario_id]

    @staticmethod
    def _public_definition(definition: ScenarioDefinition | None) -> dict[str, Any] | None:
        if definition is None:
            return None
        return {
            "id": definition.id,
            "name": definition.name,
            "service": definition.service,
            "severity": definition.severity,
            "alert_type": definition.alert_type,
            "allowed_actions": definition.allowed_actions,
            "controls": definition.controls,
        }

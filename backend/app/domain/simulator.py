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
    finding: dict[str, Any] | None = None


@dataclass
class SimulatorState:
    scenario_id: str | None = None
    alerts: list[dict[str, Any]] = field(default_factory=list)
    actions: list[dict[str, Any]] = field(default_factory=list)
    service_state: dict[str, Any] = field(default_factory=dict)
    failure_controls: dict[str, Any] = field(default_factory=dict)
    custom_scenarios: dict[str, dict[str, Any]] = field(default_factory=dict)


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
                "logs": [{"timestamp": "2026-10-22T12:00:04Z", "trace_id": "pay-7f31", "route": "POST /v1/payments/authorize", "message": "payment query exceeded 3 seconds", "level": "error"}],
                "metrics": [{"name": "p99_latency_ms", "value": 3210, "threshold": 2000, "route": "/v1/payments/authorize", "window": "5m"}],
                "deploys": [{"version": "2026.10.22", "previous_version": "2026.10.21", "commit": "8f2c1de", "changed": ["payment repository query"]}],
                "service_health": [{"service": "payments-api", "healthy": False, "dependency": "orders-db", "region": "primary"}],
            },
            allowed_actions=("rollback", "restart"),
            controls={
                "evidence_slow": ["logs"],
                "action_timeout_after_completion": ["rollback"],
                "responder_non_response": False,
                "third_party_outage": False,
            },
            initial_state={"version": "2026.10.22", "healthy": False, "p99_latency_ms": 3210},
            finding={
                "metric": "p99_latency_ms",
                "category": "deployment_regression",
                "statement": "Latency is above threshold and the latest deployment differs from the previous version.",
                "confidence": 0.92,
                "suggested_next_step": "rollback",
                "evidence_sources": ["metrics", "logs", "deploys"],
                "uncertainty": "The evidence supports a deployment regression but does not prove causation.",
            },
        ),
        "disk_pressure": ScenarioDefinition(
            id="disk_pressure",
            name="Disk pressure",
            service="orders-worker",
            severity="high",
            alert_type="disk_usage_high",
            hidden_cause="worker artifacts were not cleaned after repeated jobs",
            evidence={
                "logs": [{"timestamp": "2026-10-22T12:00:03Z", "trace_id": "ord-4c92", "job": "fulfillment-export", "message": "artifact cleanup skipped after batch completion", "level": "warn"}],
                "metrics": [{"name": "disk_usage_percent", "value": 96, "threshold": 85, "mount": "/var/lib/orders", "window": "10m"}],
                "deploys": [{"version": "2026.10.20", "previous_version": "2026.10.19", "commit": "1ab93e4", "changed": ["worker artifact retention"]}],
                "service_health": [{"service": "orders-worker", "healthy": True, "queue": "fulfillment", "region": "primary"}],
            },
            allowed_actions=("clear_disk", "restart", "scale"),
            controls={
                "evidence_slow": [],
                "action_timeout_after_completion": [],
                "responder_non_response": True,
                "third_party_outage": False,
            },
            initial_state={"disk_usage_percent": 96, "replicas": 1, "healthy": True},
            finding={
                "metric": "disk_usage_percent",
                "category": "disk_pressure",
                "statement": "Disk usage is above threshold and cleanup activity is degraded.",
                "confidence": 0.94,
                "suggested_next_step": "clear_disk",
                "evidence_sources": ["metrics", "logs"],
                "uncertainty": None,
            },
        ),
        "third_party_outage": ScenarioDefinition(
            id="third_party_outage",
            name="Third-party outage",
            service="checkout-api",
            severity="high",
            alert_type="dependency_errors_high",
            hidden_cause="external payment provider is unavailable",
            evidence={
                "logs": [{"timestamp": "2026-10-22T12:00:02Z", "trace_id": "chk-a118", "route": "POST /v1/checkout", "provider": "card-authorizer", "message": "upstream provider returned 503", "level": "error"}],
                "metrics": [{"name": "provider_error_rate", "value": 100, "threshold": 5, "provider": "card-authorizer", "window": "5m"}],
                "deploys": [{"version": "2026.10.18", "previous_version": "2026.10.17", "commit": "d301fca", "changed": ["checkout copy"]}],
                "service_health": [{"service": "checkout-api", "healthy": True, "dependency": "card-authorizer", "dependency_healthy": False}],
            },
            allowed_actions=(),
            controls={
                "evidence_slow": [],
                "action_timeout_after_completion": [],
                "responder_non_response": False,
                "third_party_outage": True,
            },
            initial_state={"provider_available": False, "healthy": True},
            finding={
                "metric": "provider_error_rate",
                "category": "third_party_outage",
                "statement": "The dependency error rate is above threshold while the local service remains healthy.",
                "confidence": 0.97,
                "suggested_next_step": "unfixable",
                "evidence_sources": ["metrics", "logs", "service_health"],
                "uncertainty": "The external dependency must recover; local remediation is not proposed.",
            },
        ),
    }


class SimulatorService:
    REQUIRED_DEFINITION_FIELDS = ("name", "service", "severity", "alert_type", "evidence", "finding")

    def __init__(self, state_path: str | None = None) -> None:
        self._definitions = scenario_definitions()
        self._state_path = state_path or os.getenv("SIMULATOR_STATE_PATH")
        self._state = self._load()
        for scenario_id, payload in self._state.custom_scenarios.items():
            try:
                self._definitions[scenario_id] = self._definition_from_payload(scenario_id, payload)
            except (KeyError, TypeError, ValueError):
                continue

    def list_scenarios(self) -> list[dict[str, Any]]:
        return [self._public_definition(definition) for definition in self._definitions.values()]

    def register_scenario(self, scenario_id: str, definition: dict[str, Any]) -> dict[str, Any]:
        if scenario_id in {"deployment_regression", "disk_pressure", "third_party_outage"}:
            raise ValueError("a built-in scenario cannot be replaced")
        parsed = self._definition_from_payload(scenario_id, definition)
        self._definitions[scenario_id] = parsed
        self._state.custom_scenarios[scenario_id] = definition
        self._save()
        return self._public_definition(parsed)

    def finding_rules(self, scenario_id: str | None) -> list[dict[str, Any]]:
        if not scenario_id or scenario_id not in self._definitions:
            return []
        finding = self._definitions[scenario_id].finding
        return [finding] if finding else []

    @classmethod
    def _definition_from_payload(cls, scenario_id: str, payload: dict[str, Any]) -> ScenarioDefinition:
        for field in cls.REQUIRED_DEFINITION_FIELDS:
            if not payload.get(field):
                raise ValueError(f"scenario definition requires {field}")
        evidence = payload["evidence"]
        if not isinstance(evidence, dict) or not evidence:
            raise ValueError("scenario evidence must be a non-empty object")
        finding = payload["finding"]
        for field in ("metric", "category", "statement", "suggested_next_step"):
            if not isinstance(finding.get(field), str) or not finding[field]:
                raise ValueError(f"scenario finding requires {field}")
        if not isinstance(finding.get("confidence"), (int, float)) or not 0 <= finding["confidence"] <= 1:
            raise ValueError("scenario finding confidence must be between 0 and 1")
        controls = payload.get("controls", {})
        return ScenarioDefinition(
            id=scenario_id,
            name=str(payload["name"]),
            service=str(payload["service"]),
            severity=str(payload["severity"]),
            alert_type=str(payload["alert_type"]),
            hidden_cause=str(payload.get("hidden_cause", "")),
            evidence={str(key): list(value) for key, value in evidence.items()},
            allowed_actions=tuple(payload.get("allowed_actions", ())),
            controls={
                "evidence_slow": list(controls.get("evidence_slow", [])),
                "action_timeout_after_completion": list(controls.get("action_timeout_after_completion", [])),
                "responder_non_response": bool(controls.get("responder_non_response", False)),
                "third_party_outage": bool(controls.get("third_party_outage", False)),
            },
            initial_state=dict(payload.get("initial_state", {})),
            finding={
                "metric": finding["metric"],
                "category": finding["category"],
                "statement": finding["statement"],
                "confidence": float(finding["confidence"]),
                "suggested_next_step": finding["suggested_next_step"],
                "evidence_sources": list(finding.get("evidence_sources", ["metrics", "logs"])),
                "uncertainty": finding.get("uncertainty"),
            },
        )

    def select_scenario(self, scenario_id: str) -> dict[str, Any]:
        definition = self._definition(scenario_id)
        self._state = SimulatorState(
            scenario_id=scenario_id,
            service_state=dict(definition.initial_state),
            failure_controls=self._controls(definition),
            custom_scenarios=dict(self._state.custom_scenarios),
        )
        self._save()
        return self.state()

    def reset(self) -> dict[str, Any]:
        scenario_id = self._state.scenario_id
        definition = self._definition(scenario_id) if scenario_id else None
        self._state = SimulatorState(
            scenario_id=scenario_id,
            service_state=dict(definition.initial_state) if definition else {},
            failure_controls=self._controls(definition) if definition else {},
            custom_scenarios=dict(self._state.custom_scenarios),
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
            "failure_controls": self._state.failure_controls,
            "actions": self._state.actions,
        }

    def set_failure_controls(self, responder_available: bool | None = None,
                             third_party_available: bool | None = None) -> dict[str, Any]:
        if responder_available is not None:
            self._state.failure_controls["responder_available"] = responder_available
        if third_party_available is not None:
            self._state.failure_controls["third_party_available"] = third_party_available
        self._save()
        return self.state()

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

        source_time = datetime.now(timezone.utc)
        if late:
            source_time -= timedelta(hours=1)
        lifecycles = ["firing", "resolved"] if flapping else ["firing"]
        deliveries = []
        for lifecycle_index, lifecycle in enumerate(lifecycles):
            source_event_id = str(uuid4())
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
                    "source": "simulator",
                    "labels": {"scenario": definition.id},
                    "description": f"{definition.name} alert triggered",
                    "correlation_key": definition.id,
                    "source_time": (source_time + timedelta(seconds=lifecycle_index)).isoformat(),
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
        if definition.controls["third_party_outage"] and not self._state.failure_controls.get("third_party_available", False):
            availability = "unavailable" if source_type == "service_health" else availability
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

    def preview_action(self, scenario_id: str, action_type: str, target: str,
                       parameters: dict[str, Any]) -> dict[str, Any]:
        self.validate_action(scenario_id, action_type, target, parameters)
        definition = self._definition(scenario_id)
        state_before = dict(self._state.service_state) if self._state.scenario_id == scenario_id else dict(definition.initial_state)
        state_after = self._project_action(action_type, dict(state_before), parameters)
        changes = {
            key: {"before": state_before.get(key), "after": value}
            for key, value in state_after.items()
            if state_before.get(key) != value
        }
        return {
            "sandboxed": True,
            "scenario_id": scenario_id,
            "action_type": action_type,
            "target": target,
            "state_before": state_before,
            "state_after": state_after,
            "changes": changes,
        }

    def validate_action(self, scenario_id: str, action_type: str, target: str,
                        parameters: dict[str, Any]) -> None:
        definition = self._definition(scenario_id)
        if action_type not in definition.allowed_actions:
            raise ValueError("action is not allowed for the selected scenario")
        if target != definition.service:
            raise ValueError("action target does not match the selected scenario")
        if action_type == "scale":
            replicas = parameters.get("replicas")
            if not isinstance(replicas, int) or replicas < 1:
                raise ValueError("scale requires a positive integer replicas parameter")

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
        state = self._project_action(action_type, state, parameters)
        self._state.service_state = state
        return state

    def _project_action(self, action_type: str, state: dict[str, Any], parameters: dict[str, Any]) -> dict[str, Any]:
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
                failure_controls=payload.get("failure_controls", {}),
                custom_scenarios=payload.get("custom_scenarios", {}),
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
    def _controls(definition: ScenarioDefinition | None) -> dict[str, Any]:
        if definition is None:
            return {}
        return {
            "responder_available": not definition.controls["responder_non_response"],
            "third_party_available": not definition.controls["third_party_outage"],
        }

    @staticmethod
    def _public_definition(definition: ScenarioDefinition | None) -> dict[str, Any] | None:
        if definition is None:
            return None
        public = {
            "id": definition.id,
            "name": definition.name,
            "service": definition.service,
            "severity": definition.severity,
            "alert_type": definition.alert_type,
            "allowed_actions": definition.allowed_actions,
            "controls": definition.controls,
        }
        if definition.finding:
            public["finding"] = {
                "metric": definition.finding["metric"],
                "category": definition.finding["category"],
                "suggested_next_step": definition.finding["suggested_next_step"],
            }
        return public

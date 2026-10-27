from typing import Any
from uuid import UUID

from fastapi import APIRouter, Query
from pydantic import BaseModel, Field

from app.application.simulator import simulator_service
from app.application.incident import alert_pipeline_service
from app.api.errors import map_error


router = APIRouter(prefix="/api/v1/simulator", tags=["simulator"])


class ScenarioRequest(BaseModel):
    scenario_id: str
    definition: dict[str, Any] | None = None


class AlertRequest(BaseModel):
    scenario_id: str | None = None
    duplicate_count: int = Field(default=1, ge=1, le=5)
    late: bool = False
    flapping: bool = False
    out_of_order: bool = False
    delayed_seconds: int = Field(default=0, ge=0, le=300)


class ActionRequest(BaseModel):
    action_type: str
    target: str
    parameters: dict[str, Any] = Field(default_factory=dict)
    idempotency_key: str | None = Field(default=None, min_length=1)


class FailureControlRequest(BaseModel):
    responder_available: bool | None = None
    third_party_available: bool | None = None


@router.get("/scenarios")
def list_scenarios() -> list[dict[str, Any]]:
    return simulator_service.list_scenarios()


@router.post("/scenarios")
@map_error(404)
def select_scenario(request: ScenarioRequest) -> dict[str, Any]:
    if request.definition is not None:
        simulator_service.register_scenario(request.scenario_id, request.definition)
    return simulator_service.select_scenario(request.scenario_id)


@router.post("/reset")
def reset_scenario() -> dict[str, Any]:
    return simulator_service.reset()


@router.get("/state")
def get_state() -> dict[str, Any]:
    return simulator_service.state()


@router.post("/failure-controls")
def set_failure_controls(request: FailureControlRequest) -> dict[str, Any]:
    return simulator_service.set_failure_controls(request.responder_available, request.third_party_available)


@router.post("/alerts")
@map_error(400)
def trigger_alert(request: AlertRequest) -> dict[str, Any]:
    result = simulator_service.trigger_alert(
        request.scenario_id,
        request.duplicate_count,
        request.late,
        request.flapping,
        request.out_of_order,
        request.delayed_seconds,
    )
    result["accepted"] = [alert_pipeline_service.accept(delivery) for delivery in result["deliveries"]]
    return result


@router.get("/evidence")
@map_error(400)
def query_evidence(source_type: str = Query(...)) -> dict[str, Any]:
    return simulator_service.query_evidence(source_type)


@router.post("/actions")
@map_error(400)
def execute_action(request: ActionRequest) -> dict[str, Any]:
    return simulator_service.execute_action(
        request.action_type,
        request.target,
        request.parameters,
        request.idempotency_key,
    )


@router.post("/actions/{action_id}/verify")
@map_error(404)
def verify_action(action_id: UUID) -> dict[str, Any]:
    return simulator_service.verify_action(action_id)

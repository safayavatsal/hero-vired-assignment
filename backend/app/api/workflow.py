from typing import Any
from uuid import UUID

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.application.workflow import WorkflowService


router = APIRouter(prefix="/api/v1", tags=["workflow"])
workflow_service = WorkflowService()


class PageRequest(BaseModel):
    responder: str | None = Field(default=None, min_length=1)
    fallback_responder: str | None = Field(default=None, min_length=1)
    deadline_seconds: int = Field(default=300, ge=1, le=3600)


class PageResponse(BaseModel):
    response_type: str = Field(min_length=1)
    response_text: str | None = None
    expected_version: int | None = Field(default=None, ge=1)


class ActionRequest(BaseModel):
    scenario_id: str = Field(min_length=1)
    action_type: str = Field(min_length=1)
    target: str = Field(min_length=1)
    parameters: dict[str, Any] = Field(default_factory=dict)
    idempotency_key: str = Field(min_length=1)
    approval_seconds: int = Field(default=300, ge=1, le=3600)


class ActionPreviewRequest(BaseModel):
    scenario_id: str = Field(min_length=1)
    action_type: str = Field(min_length=1)
    target: str = Field(min_length=1)
    parameters: dict[str, Any] = Field(default_factory=dict)


class ActionDecision(BaseModel):
    approved: bool
    responder: str = Field(min_length=1)
    expected_version: int | None = Field(default=None, ge=1)


@router.post("/incidents/{incident_id}/page")
def create_page(incident_id: UUID, request: PageRequest) -> dict[str, Any]:
    try:
        return workflow_service.create_page(incident_id, request.responder, request.fallback_responder, request.deadline_seconds)
    except Exception as error:
        raise HTTPException(status_code=400, detail=str(error)) from error


@router.post("/pages/{page_id}/respond")
def respond_page(page_id: UUID, request: PageResponse) -> dict[str, Any]:
    try:
        return workflow_service.respond(page_id, request.response_type, request.response_text, request.expected_version)
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error


@router.get("/incidents/{incident_id}/pages")
def list_pages(incident_id: UUID) -> list[dict[str, Any]]:
    return workflow_service.list_pages(incident_id)


@router.post("/incidents/{incident_id}/actions")
def propose_action(incident_id: UUID, request: ActionRequest) -> dict[str, Any]:
    try:
        return workflow_service.propose_action(incident_id, request.scenario_id, request.action_type, request.target,
                                               request.parameters, request.idempotency_key, request.approval_seconds)
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error


@router.post("/incidents/{incident_id}/actions/preview")
def preview_action(incident_id: UUID, request: ActionPreviewRequest) -> dict[str, Any]:
    try:
        return workflow_service.preview_action(incident_id, request.scenario_id, request.action_type, request.target, request.parameters)
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error


@router.post("/actions/{action_id}/decision")
def decide_action(action_id: UUID, request: ActionDecision) -> dict[str, Any]:
    try:
        return workflow_service.decide_action(action_id, request.approved, request.responder, request.expected_version)
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error


@router.get("/incidents/{incident_id}/actions")
def list_actions(incident_id: UUID) -> list[dict[str, Any]]:
    return workflow_service.list_actions(incident_id)


@router.post("/actions/{action_id}/execute")
def execute_action(action_id: UUID) -> dict[str, Any]:
    try:
        return workflow_service.execute_action(action_id)
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error


@router.post("/actions/{action_id}/verify")
def verify_action(action_id: UUID) -> dict[str, Any]:
    try:
        return workflow_service.verify_action(action_id)
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error


@router.post("/actions/{action_id}/reconcile")
def reconcile_action(action_id: UUID) -> dict[str, Any]:
    try:
        return workflow_service.reconcile_action(action_id)
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error

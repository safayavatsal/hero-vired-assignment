from typing import Any, Literal
from uuid import UUID

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.application.incident import investigation_service
from app.application.evidence_tools import evidence_tool_catalog


router = APIRouter(prefix="/api/v1", tags=["investigations"])


class InvestigationRequest(BaseModel):
    scenario_id: str = Field(min_length=1)
    mode: Literal["standard", "deeper"] = "standard"


@router.post("/incidents/{incident_id}/investigate")
def investigate(incident_id: UUID, request: InvestigationRequest) -> dict[str, Any]:
    try:
        return investigation_service.enqueue(incident_id, request.scenario_id, request.mode)
    except ValueError as error:
        status_code = 404 if str(error) == "incident not found" else 409
        raise HTTPException(status_code=status_code, detail=str(error)) from error


@router.get("/investigation-tools")
def list_investigation_tools() -> dict[str, Any]:
    return {"tools": evidence_tool_catalog()}


@router.get("/incidents/{incident_id}/evidence")
def get_investigation(incident_id: UUID) -> dict[str, Any]:
    try:
        return investigation_service.get_status(incident_id)
    except ValueError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error

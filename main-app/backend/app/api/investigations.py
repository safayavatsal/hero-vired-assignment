from typing import Any, Literal
from uuid import UUID

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from app.application.incident import investigation_service
from app.application.evidence_tools import evidence_tool_catalog
from app.application.auth import Principal, require_role
from app.api.errors import map_error


router = APIRouter(prefix="/api/v1", tags=["investigations"])


class InvestigationRequest(BaseModel):
    scenario_id: str = Field(min_length=1)
    mode: Literal["standard", "deeper"] = "standard"


@router.post("/incidents/{incident_id}/investigate")
@map_error(lambda error: 404 if str(error) == "incident not found" else 409)
def investigate(incident_id: UUID, request: InvestigationRequest,
                _principal: Principal = Depends(require_role("responder"))) -> dict[str, Any]:
    return investigation_service.enqueue(incident_id, request.scenario_id, request.mode)


@router.get("/investigation-tools")
def list_investigation_tools() -> dict[str, Any]:
    return {"tools": evidence_tool_catalog()}


@router.get("/incidents/{incident_id}/evidence")
@map_error(404)
def get_investigation(incident_id: UUID) -> dict[str, Any]:
    return investigation_service.get_status(incident_id)

from typing import Any
from uuid import UUID

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.application.incident import investigation_service


router = APIRouter(prefix="/api/v1", tags=["investigations"])


class InvestigationRequest(BaseModel):
    scenario_id: str = Field(min_length=1)


@router.post("/incidents/{incident_id}/investigate")
def investigate(incident_id: UUID, request: InvestigationRequest) -> dict[str, Any]:
    try:
        return investigation_service.investigate(incident_id, request.scenario_id)
    except ValueError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error


@router.get("/incidents/{incident_id}/evidence")
def get_investigation(incident_id: UUID) -> dict[str, Any]:
    try:
        return investigation_service.get(incident_id)
    except ValueError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error

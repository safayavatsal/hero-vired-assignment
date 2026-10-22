from datetime import datetime
from typing import Any
from uuid import UUID

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.application.incident import alert_pipeline_service


router = APIRouter(prefix="/api/v1", tags=["incidents"])


class AlertWebhook(BaseModel):
    source_event_id: str = Field(min_length=1)
    source: str = Field(min_length=1)
    service: str = Field(min_length=1)
    severity: str = Field(min_length=1)
    alert_type: str = Field(min_length=1)
    source_time: datetime
    labels: dict[str, str] = Field(default_factory=dict)
    description: str = ""
    lifecycle: str = "firing"
    correlation_key: str | None = None


@router.post("/alerts")
def create_alert(alert: AlertWebhook) -> dict[str, Any]:
    return alert_pipeline_service.accept(alert.model_dump())


@router.get("/incidents")
def list_incidents() -> list[dict[str, Any]]:
    return alert_pipeline_service.list_incidents()


@router.get("/incidents/{incident_id}")
def get_incident(incident_id: UUID) -> dict[str, Any]:
    try:
        return alert_pipeline_service.get_incident(incident_id)
    except ValueError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error


@router.get("/incidents/{incident_id}/timeline")
def get_timeline(incident_id: UUID) -> list[dict[str, Any]]:
    try:
        return alert_pipeline_service.get_timeline(incident_id)
    except ValueError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error

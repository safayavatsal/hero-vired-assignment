from datetime import datetime
from typing import Any
from uuid import UUID

from fastapi import APIRouter
from pydantic import BaseModel, Field

from app.application.incident import alert_pipeline_service
from app.api.errors import map_error


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


class IncidentTransition(BaseModel):
    target_status: str = Field(min_length=1)
    expected_version: int | None = Field(default=None, ge=1)


@router.post("/alerts")
def create_alert(alert: AlertWebhook) -> dict[str, Any]:
    return alert_pipeline_service.accept(alert.model_dump())


@router.get("/incidents")
def list_incidents() -> list[dict[str, Any]]:
    return alert_pipeline_service.list_incidents()


@router.get("/incidents/{incident_id}")
@map_error(404)
def get_incident(incident_id: UUID) -> dict[str, Any]:
    return alert_pipeline_service.get_incident(incident_id)


@router.get("/incidents/{incident_id}/timeline")
@map_error(404)
def get_timeline(incident_id: UUID) -> list[dict[str, Any]]:
    return alert_pipeline_service.get_timeline(incident_id)


@router.post("/incidents/{incident_id}/status")
@map_error(lambda error: 404 if str(error) == "incident not found" else 409)
def transition_incident(incident_id: UUID, request: IncidentTransition) -> dict[str, Any]:
    return alert_pipeline_service.transition(
        incident_id, request.target_status, request.expected_version
    )

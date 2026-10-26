from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.application.kubernetes_analyzers import analyze_resources, analyzer_catalog


router = APIRouter(prefix="/api/v1/kubernetes", tags=["kubernetes"])


class KubernetesAnalysisRequest(BaseModel):
    resources: list[dict[str, Any]] = Field(default_factory=list)
    namespace: str | None = None
    resource_type: str | None = None
    resource_name: str | None = None
    labels: dict[str, str] = Field(default_factory=dict)
    analyzers: list[str] | None = None


@router.get("/analyzers")
def list_analyzers() -> dict[str, Any]:
    return {"analyzers": analyzer_catalog()}


@router.post("/analyze")
def analyze(request: KubernetesAnalysisRequest) -> dict[str, Any]:
    try:
        return analyze_resources(
            request.resources,
            namespace=request.namespace,
            resource_type=request.resource_type,
            resource_name=request.resource_name,
            labels=request.labels,
            analyzer_names=request.analyzers,
        )
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error

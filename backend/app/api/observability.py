from typing import Any

from fastapi import APIRouter

from app.application.observability import runtime_metrics


router = APIRouter(prefix="/api/v1", tags=["observability"])


@router.get("/metrics")
def metrics() -> dict[str, Any]:
    return runtime_metrics.snapshot()

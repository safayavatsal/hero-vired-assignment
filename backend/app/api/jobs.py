from typing import Any

from fastapi import APIRouter

from app.application.job_queue import JobRepository


router = APIRouter(prefix="/api/v1/jobs", tags=["jobs"])


@router.get("/metrics")
def queue_metrics() -> dict[str, Any]:
    return JobRepository().metrics()

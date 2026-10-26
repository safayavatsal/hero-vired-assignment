from typing import Any

from fastapi import APIRouter, Depends

from app.application.auth import Principal, require_role


router = APIRouter(prefix="/api/v1/auth", tags=["auth"])


@router.get("/context")
def auth_context(principal: Principal = Depends(require_role("viewer"))) -> dict[str, Any]:
    return {"name": principal.name, "role": principal.role}

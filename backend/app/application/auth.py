import json
import os
from dataclasses import dataclass

from fastapi import Header, HTTPException


ROLE_LEVELS = {"viewer": 1, "responder": 2, "approver": 3, "administrator": 4}


@dataclass(frozen=True)
class Principal:
    name: str
    role: str


def require_role(minimum_role: str):
    if minimum_role not in ROLE_LEVELS:
        raise ValueError("unknown operator role")

    def dependency(x_operator_token: str | None = Header(default=None)) -> Principal:
        if os.getenv("AUTH_MODE", "off").strip().lower() != "required":
            return Principal("local-operator", "administrator")
        if not x_operator_token:
            raise HTTPException(status_code=401, detail="operator token required")
        try:
            tokens = json.loads(os.getenv("OPERATOR_TOKENS", "{}"))
        except json.JSONDecodeError as error:
            raise HTTPException(status_code=503, detail="operator authentication is unavailable") from error
        identity = tokens.get(x_operator_token)
        if not isinstance(identity, dict) or identity.get("role") not in ROLE_LEVELS or not identity.get("name"):
            raise HTTPException(status_code=401, detail="operator token is invalid")
        if ROLE_LEVELS[identity["role"]] < ROLE_LEVELS[minimum_role]:
            raise HTTPException(status_code=403, detail="operator role is not permitted")
        return Principal(identity["name"], identity["role"])

    return dependency

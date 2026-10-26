import json

from fastapi.testclient import TestClient

from app.main import app


def test_auth_context_is_local_administrator_when_auth_is_disabled(monkeypatch) -> None:
    monkeypatch.delenv("AUTH_MODE", raising=False)
    response = TestClient(app).get("/api/v1/auth/context")

    assert response.status_code == 200
    assert response.json() == {"name": "local-operator", "role": "administrator"}


def test_auth_context_requires_a_token_when_enabled(monkeypatch) -> None:
    monkeypatch.setenv("AUTH_MODE", "required")
    monkeypatch.setenv("OPERATOR_TOKENS", json.dumps({"viewer-token": {"name": "Read Only", "role": "viewer"}}))

    response = TestClient(app).get("/api/v1/auth/context")

    assert response.status_code == 401


def test_auth_context_returns_configured_principal(monkeypatch) -> None:
    monkeypatch.setenv("AUTH_MODE", "required")
    monkeypatch.setenv("OPERATOR_TOKENS", json.dumps({"responder-token": {"name": "On Call", "role": "responder"}}))

    response = TestClient(app).get("/api/v1/auth/context", headers={"X-Operator-Token": "responder-token"})

    assert response.status_code == 200
    assert response.json() == {"name": "On Call", "role": "responder"}


def test_auth_context_rejects_unknown_token(monkeypatch) -> None:
    monkeypatch.setenv("AUTH_MODE", "required")
    monkeypatch.setenv("OPERATOR_TOKENS", json.dumps({"viewer-token": {"name": "Read Only", "role": "viewer"}}))

    response = TestClient(app).get("/api/v1/auth/context", headers={"X-Operator-Token": "bad-token"})

    assert response.status_code == 401

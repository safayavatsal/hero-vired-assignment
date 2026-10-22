from app.application import external_boundaries


def test_ownership_gateway_is_opt_in_and_validates_response(monkeypatch) -> None:
    monkeypatch.setenv("OWNERSHIP_GATEWAY_URL", "http://ownership.test/resolve")
    monkeypatch.setattr(external_boundaries, "_request_json", lambda *_args: {"primary_responder": "oncall-a", "fallback_responder": "oncall-b"})

    result = external_boundaries.OwnershipGateway().resolve("payments-api", "critical")

    assert result == {"responder": "oncall-a", "fallback_responder": "oncall-b"}


def test_notification_gateway_uses_bearer_token_without_exposing_it(monkeypatch) -> None:
    monkeypatch.setenv("NOTIFICATION_GATEWAY_URL", "http://notify.test/page")
    monkeypatch.setenv("NOTIFICATION_GATEWAY_TOKEN", "secret")
    captured = {}

    def request(url, token, payload):
        captured.update(url=url, token=token, payload=payload)
        return {"status": "delivered", "id": "delivery-1"}

    monkeypatch.setattr(external_boundaries, "_request_json", request)
    result = external_boundaries.NotificationGateway().deliver({"page_id": "page-1"})

    assert result == {"status": "delivered", "id": "delivery-1"}
    assert captured == {"url": "http://notify.test/page", "token": "secret", "payload": {"page_id": "page-1"}}


def test_action_executor_is_noop_when_not_configured(monkeypatch) -> None:
    monkeypatch.delenv("ACTION_EXECUTOR_URL", raising=False)

    assert external_boundaries.ActionExecutorGateway().reconcile({"id": "action-1", "idempotency_key": "key-1", "target": "payments-api"}) is None

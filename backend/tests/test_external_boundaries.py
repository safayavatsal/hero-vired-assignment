import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from threading import Thread

from app.application import external_boundaries


def test_ownership_gateway_is_opt_in_and_validates_response(monkeypatch) -> None:
    monkeypatch.setenv("OWNERSHIP_GATEWAY_URL", "http://ownership.test/resolve")
    monkeypatch.setattr(external_boundaries, "_request_json", lambda *_args: {"primary_responder": "oncall-a", "fallback_responder": "oncall-b"})

    result = external_boundaries.OwnershipGateway().resolve("payments-api", "critical")

    assert result == {"responder": "oncall-a", "fallback_responder": "oncall-b"}


def test_ownership_gateway_preserves_owner_addresses(monkeypatch) -> None:
    monkeypatch.setenv("OWNERSHIP_GATEWAY_URL", "http://ownership.test/resolve")
    monkeypatch.setattr(external_boundaries, "_request_json", lambda *_args: {
        "primary_responder": "oncall-a", "fallback_responder": "oncall-b",
        "responder_email": "a@example.test", "fallback_email": "b@example.test",
    })

    assert external_boundaries.OwnershipGateway().resolve("payments-api", "critical") == {
        "responder": "oncall-a", "fallback_responder": "oncall-b",
        "responder_email": "a@example.test", "fallback_email": "b@example.test",
    }


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


def test_notification_gateway_delivers_local_email(monkeypatch) -> None:
    monkeypatch.delenv("NOTIFICATION_GATEWAY_URL", raising=False)
    monkeypatch.setenv("NOTIFICATION_SMTP_HOST", "mail.test")
    monkeypatch.setenv("NOTIFICATION_EMAIL_TO", "oncall@demo.local")
    captured = {}

    class SMTP:
        def __init__(self, host, port, timeout):
            captured.update(host=host, port=port, timeout=timeout)

        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return False

        def send_message(self, message):
            captured["message"] = message

    monkeypatch.setattr(external_boundaries.smtplib, "SMTP", SMTP)
    result = external_boundaries.NotificationGateway().deliver({
        "incident_id": "incident-1",
        "service": "checkout-api",
        "severity": "critical",
        "summary": "Payment authorization failed",
        "evidence_summary": "The provider is unavailable.",
        "suggested_next_step": "failover",
    })

    assert result["status"] == "delivered"
    assert captured["host"] == "mail.test"
    assert captured["message"]["To"] == "oncall@demo.local"
    body = captured["message"].get_content()
    assert "Incident ID: incident-1" in body
    assert "The provider is unavailable." in body
    assert "Open incident console:" in body


def test_action_executor_is_noop_when_not_configured(monkeypatch) -> None:
    monkeypatch.delenv("ACTION_EXECUTOR_URL", raising=False)

    assert external_boundaries.ActionExecutorGateway().reconcile({"id": "action-1", "idempotency_key": "key-1", "target": "payments-api"}) is None


def test_external_boundaries_use_live_http_contracts(monkeypatch) -> None:
    requests = []

    class Handler(BaseHTTPRequestHandler):
        def do_POST(self) -> None:
            length = int(self.headers["Content-Length"])
            requests.append((self.path, self.headers.get("Authorization"), json.loads(self.rfile.read(length))))
            responses = {
                "/ownership": {"primary_responder": "oncall-a", "fallback_responder": "oncall-b"},
                "/notify": {"status": "delivered", "id": "delivery-1"},
                "/action": {"status": "verified", "verified": True},
            }
            body = json.dumps(responses[self.path]).encode()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def log_message(self, *_args) -> None:
            return

    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    base_url = f"http://127.0.0.1:{server.server_port}"
    try:
        monkeypatch.setenv("OWNERSHIP_GATEWAY_URL", f"{base_url}/ownership")
        monkeypatch.setenv("OWNERSHIP_GATEWAY_TOKEN", "ownership-token")
        monkeypatch.setenv("NOTIFICATION_GATEWAY_URL", f"{base_url}/notify")
        monkeypatch.setenv("NOTIFICATION_GATEWAY_TOKEN", "notification-token")
        monkeypatch.setenv("ACTION_EXECUTOR_URL", f"{base_url}/action")
        monkeypatch.setenv("ACTION_EXECUTOR_TOKEN", "action-token")

        assert external_boundaries.OwnershipGateway().resolve("payments-api", "critical") == {
            "responder": "oncall-a", "fallback_responder": "oncall-b"
        }
        assert external_boundaries.NotificationGateway().deliver({"page_id": "page-1"}) == {
            "status": "delivered", "id": "delivery-1"
        }
        assert external_boundaries.ActionExecutorGateway().reconcile({
            "id": "action-1", "idempotency_key": "key-1", "target": "payments-api"
        }) == {"status": "verified", "verified": True}
        assert requests == [
            ("/ownership", "Bearer ownership-token", {"service": "payments-api", "severity": "critical"}),
            ("/notify", "Bearer notification-token", {"page_id": "page-1"}),
            ("/action", "Bearer action-token", {"action_id": "action-1", "idempotency_key": "key-1", "target": "payments-api"}),
        ]
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)


def test_external_boundary_timeout_is_configurable(monkeypatch) -> None:
    monkeypatch.setenv("EXTERNAL_BOUNDARY_TIMEOUT_SECONDS", "0.2")
    monkeypatch.setenv("NOTIFICATION_GATEWAY_URL", "http://notify.test/page")
    captured = {}

    class Response:
        def read(self):
            return b'{}'

        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return False

    def request(_request, timeout):
        captured["timeout"] = timeout
        return Response()

    monkeypatch.setattr(external_boundaries, "urlopen", request)
    external_boundaries.NotificationGateway().deliver({"page_id": "page-1"})

    assert captured == {"timeout": 0.2}

import json
import os
import subprocess
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path


ROOT = Path(__file__).parents[2]


class ScenarioStub(BaseHTTPRequestHandler):
    requests: list[tuple[str, dict]] = []

    def do_POST(self) -> None:  # noqa: N802
        length = int(self.headers["content-length"])
        payload = json.loads(self.rfile.read(length))
        self.requests.append((self.path, payload))
        if self.path.endswith("/scenarios"):
            response = {"scenario": {"id": payload["scenario_id"]}}
        elif self.path.endswith("/alerts"):
            response = {"accepted": [{"incident": {"id": "incident-script-1"}}]}
        else:
            self.send_error(404)
            return
        body = json.dumps(response).encode()
        self.send_response(200)
        self.send_header("content-type", "application/json")
        self.send_header("content-length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *_args) -> None:
        return


def test_add_scenario_registers_and_triggers_one_alert(tmp_path) -> None:
    ScenarioStub.requests = []
    server = ThreadingHTTPServer(("127.0.0.1", 0), ScenarioStub)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        definition = {
            "scenario_id": "queue_backlog",
            "definition": {
                "name": "Queue backlog",
                "service": "orders-worker",
                "severity": "high",
                "alert_type": "queue_depth_high",
                "evidence": {"metrics": [{"name": "queue_depth", "value": 90}]},
                "finding": {
                    "metric": "queue_depth",
                    "category": "queue_backlog",
                    "statement": "Queue depth is above threshold.",
                    "confidence": 0.9,
                    "suggested_next_step": "scale",
                },
            },
        }
        definition_path = tmp_path / "queue-backlog.json"
        definition_path.write_text(json.dumps(definition), encoding="utf-8")
        environment = {**os.environ, "BASE_URL": f"http://127.0.0.1:{server.server_port}"}
        result = subprocess.run(
            ["bash", str(ROOT / "scripts/add-scenario.sh"), str(definition_path)],
            cwd=ROOT,
            env=environment,
            capture_output=True,
            text=True,
            check=True,
        )

        assert result.stdout.strip() == "incident-script-1"
        assert [path for path, _payload in ScenarioStub.requests] == [
            "/api/v1/simulator/scenarios",
            "/api/v1/simulator/alerts",
        ]
        assert ScenarioStub.requests[0][1]["scenario_id"] == "queue_backlog"
        assert ScenarioStub.requests[1][1] == {"scenario_id": "queue_backlog"}
    finally:
        server.shutdown()
        thread.join(timeout=2)


def test_add_scenario_rejects_incomplete_definition_before_request(tmp_path) -> None:
    definition_path = tmp_path / "invalid.json"
    definition_path.write_text(json.dumps({"scenario_id": "incomplete", "definition": {}}), encoding="utf-8")

    result = subprocess.run(
        ["bash", str(ROOT / "scripts/add-scenario.sh"), str(definition_path)],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )

    assert result.returncode != 0
    assert "scenario definition requires name" in result.stderr

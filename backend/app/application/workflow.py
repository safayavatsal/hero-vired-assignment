import json
import os
from datetime import datetime, timedelta, timezone
from typing import Any
from uuid import UUID, uuid4

import psycopg
from psycopg.rows import dict_row
from psycopg.types.json import Jsonb

from app.application.simulator import simulator_service
from app.application.external_boundaries import ActionExecutorGateway, NotificationGateway, OwnershipGateway


DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/oncall")
ACTION_TYPES = {"restart", "rollback", "scale", "clear_disk"}

SCHEMA = """
CREATE TABLE IF NOT EXISTS pages (
    id UUID PRIMARY KEY,
    incident_id UUID NOT NULL REFERENCES incidents(id),
    level TEXT NOT NULL,
    responder TEXT NOT NULL,
    fallback_responder TEXT NOT NULL,
    status TEXT NOT NULL,
    deadline_at TIMESTAMPTZ NOT NULL,
    response_type TEXT,
    response_text TEXT,
    incident_version INTEGER NOT NULL DEFAULT 1,
    created_at TIMESTAMPTZ NOT NULL,
    updated_at TIMESTAMPTZ NOT NULL,
    UNIQUE (incident_id, level)
);
CREATE TABLE IF NOT EXISTS action_proposals (
    id UUID PRIMARY KEY,
    incident_id UUID NOT NULL REFERENCES incidents(id),
    scenario_id TEXT NOT NULL,
    action_type TEXT NOT NULL,
    target TEXT NOT NULL,
    parameters JSONB NOT NULL,
    status TEXT NOT NULL,
    approval_expires_at TIMESTAMPTZ,
    approved_by TEXT,
    idempotency_key TEXT NOT NULL UNIQUE,
    simulator_action_id UUID,
    result JSONB,
    incident_version INTEGER NOT NULL DEFAULT 1,
    created_at TIMESTAMPTZ NOT NULL,
    updated_at TIMESTAMPTZ NOT NULL
);
ALTER TABLE pages ADD COLUMN IF NOT EXISTS incident_version INTEGER NOT NULL DEFAULT 1;
ALTER TABLE action_proposals ADD COLUMN IF NOT EXISTS incident_version INTEGER NOT NULL DEFAULT 1;
"""


class WorkflowService:
    def __init__(self, database_url: str = DATABASE_URL) -> None:
        self.database_url = database_url
        self.ownership_gateway = OwnershipGateway()
        self.notification_gateway = NotificationGateway()
        self.action_executor_gateway = ActionExecutorGateway()

    def initialize(self) -> None:
        with psycopg.connect(self.database_url, row_factory=dict_row) as connection:
            connection.execute(SCHEMA)
            now = datetime.now(timezone.utc)
            running = connection.execute(
                "UPDATE action_proposals SET status = 'unknown', updated_at = %s WHERE status = 'running' RETURNING incident_id, id",
                (now,),
            ).fetchall()
            for action in running:
                self._timeline(connection, action["incident_id"], "action_recovered_unknown", {"action_id": str(action["id"])})
            overdue = connection.execute(
                "SELECT * FROM pages WHERE level = 'primary' AND status = 'delivered' AND deadline_at <= %s FOR UPDATE",
                (now,),
            ).fetchall()
            for page in overdue:
                connection.execute("UPDATE pages SET status = 'escalated', response_type = 'timeout', updated_at = %s WHERE id = %s", (now, page["id"]))
                fallback_id = uuid4()
                connection.execute(
                    """INSERT INTO pages
                    (id, incident_id, level, responder, fallback_responder, status, deadline_at, created_at, updated_at, incident_version)
                    VALUES (%s, %s, 'fallback', %s, %s, 'delivered', %s, %s, %s, %s)
                    ON CONFLICT (incident_id, level) DO NOTHING""",
                    (fallback_id, page["incident_id"], page["fallback_responder"], page["fallback_responder"],
                     now + timedelta(seconds=300), now, now, page["incident_version"]),
                )
                self._timeline(connection, page["incident_id"], "page_recovered_escalated", {"page_id": str(page["id"])})

    def create_page(self, incident_id: UUID, responder: str | None, fallback: str | None, deadline_seconds: int) -> dict[str, Any]:
        incident = self._incident(incident_id)
        ownership = self.ownership_gateway.resolve(incident["service"], incident["severity"])
        responder = responder or (ownership or {}).get("responder") or "primary-oncall"
        fallback = fallback or (ownership or {}).get("fallback_responder") or "secondary-oncall"
        now = datetime.now(timezone.utc)
        deadline = now + timedelta(seconds=deadline_seconds)
        with psycopg.connect(self.database_url, row_factory=dict_row) as connection:
            existing = connection.execute(
                "SELECT * FROM pages WHERE incident_id = %s AND level = 'primary'", (incident_id,)
            ).fetchone()
            if existing:
                return {"duplicate": True, "page": self._page(existing)}
            page_id = uuid4()
            delivery = self.notification_gateway.deliver({
                "page_id": str(page_id), "incident_id": str(incident_id), "responder": responder,
                "fallback_responder": fallback, "summary": incident["summary"], "severity": incident["severity"],
            })
            connection.execute(
                """INSERT INTO pages
                (id, incident_id, level, responder, fallback_responder, status, deadline_at, created_at, updated_at, incident_version)
                VALUES (%s, %s, 'primary', %s, %s, 'delivered', %s, %s, %s, %s)""",
                (page_id, incident_id, responder, fallback, deadline, now, now, incident["version"]),
            )
            timeline = {"page_id": str(page_id), "responder": responder}
            if delivery and delivery.get("id"):
                timeline["delivery_id"] = delivery["id"]
            self._timeline(connection, incident_id, "page_delivered", timeline)
            return {"duplicate": False, "page": self._get_page(connection, page_id)}

    def list_pages(self, incident_id: UUID) -> list[dict[str, Any]]:
        with psycopg.connect(self.database_url, row_factory=dict_row) as connection:
            return [self._page(row) for row in connection.execute(
                "SELECT * FROM pages WHERE incident_id = %s ORDER BY created_at", (incident_id,)
            ).fetchall()]

    def respond(self, page_id: UUID, response_type: str, response_text: str | None = None,
                expected_version: int | None = None) -> dict[str, Any]:
        if response_type not in {"acknowledge", "reply", "timeout"}:
            raise ValueError("unsupported page response")
        now = datetime.now(timezone.utc)
        with psycopg.connect(self.database_url, row_factory=dict_row) as connection:
            page = connection.execute("SELECT * FROM pages WHERE id = %s FOR UPDATE", (page_id,)).fetchone()
            if page is None:
                raise ValueError("page not found")
            self._check_version(connection, page["incident_id"], expected_version)
            if page["status"] in {"acknowledged", "replied", "escalated"}:
                return self._page(page)
            if response_type == "timeout":
                connection.execute(
                    "UPDATE pages SET status = 'escalated', response_type = %s, updated_at = %s WHERE id = %s",
                    (response_type, now, page_id),
                )
                self._timeline(connection, page["incident_id"], "page_timeout", {"page_id": str(page_id)})
                fallback_id = uuid4()
                connection.execute(
                    """INSERT INTO pages
                    (id, incident_id, level, responder, fallback_responder, status, deadline_at, created_at, updated_at, incident_version)
                    VALUES (%s, %s, 'fallback', %s, %s, 'delivered', %s, %s, %s, %s)""",
                    (fallback_id, page["incident_id"], page["fallback_responder"], page["fallback_responder"],
                     now + timedelta(seconds=300), now, now, page["incident_version"]),
                )
                self._timeline(connection, page["incident_id"], "page_escalated", {"from_page_id": str(page_id), "page_id": str(fallback_id)})
                return {"page": self._get_page(connection, page_id), "escalated_page": self._get_page(connection, fallback_id)}
            status = "acknowledged" if response_type == "acknowledge" else "replied"
            connection.execute(
                "UPDATE pages SET status = %s, response_type = %s, response_text = %s, updated_at = %s WHERE id = %s",
                (status, response_type, response_text, now, page_id),
            )
            self._timeline(connection, page["incident_id"], "page_response", {"page_id": str(page_id), "response_type": response_type})
            return self._get_page(connection, page_id)

    def propose_action(self, incident_id: UUID, scenario_id: str, action_type: str, target: str,
                       parameters: dict[str, Any], idempotency_key: str, approval_seconds: int) -> dict[str, Any]:
        if action_type not in ACTION_TYPES:
            raise ValueError("unsupported action type")
        incident = self._incident(incident_id)
        if incident["status"] not in {"investigating", "awaiting_human"}:
            raise ValueError("investigation is required before proposing an action")
        scenario = simulator_service.select_scenario(scenario_id)["scenario"]
        if scenario["service"] != incident["service"]:
            raise ValueError("selected scenario does not match the incident service")
        simulator_service.validate_action(scenario_id, action_type, target, parameters)
        now = datetime.now(timezone.utc)
        with psycopg.connect(self.database_url, row_factory=dict_row) as connection:
            existing = connection.execute("SELECT * FROM action_proposals WHERE idempotency_key = %s", (idempotency_key,)).fetchone()
            if existing:
                return self._action(existing)
            action_id = uuid4()
            connection.execute(
                """INSERT INTO action_proposals
                (id, incident_id, scenario_id, action_type, target, parameters, status, approval_expires_at,
                 idempotency_key, created_at, updated_at, incident_version)
                VALUES (%s, %s, %s, %s, %s, %s, 'pending_approval', %s, %s, %s, %s, %s)""",
                (action_id, incident_id, scenario_id, action_type, target, Jsonb(parameters),
                 now + timedelta(seconds=approval_seconds), idempotency_key, now, now, incident["version"]),
            )
            self._timeline(connection, incident_id, "action_proposed", {"action_id": str(action_id), "action_type": action_type, "target": target})
            return self._get_action(connection, action_id)

    def _incident(self, incident_id: UUID) -> dict[str, Any]:
        from app.application.incident import alert_pipeline_service

        return alert_pipeline_service.get_incident(incident_id)

    def list_actions(self, incident_id: UUID) -> list[dict[str, Any]]:
        with psycopg.connect(self.database_url, row_factory=dict_row) as connection:
            return [self._action(row) for row in connection.execute(
                "SELECT * FROM action_proposals WHERE incident_id = %s ORDER BY created_at", (incident_id,)
            ).fetchall()]

    def decide_action(self, action_id: UUID, approved: bool, responder: str,
                      expected_version: int | None = None) -> dict[str, Any]:
        now = datetime.now(timezone.utc)
        with psycopg.connect(self.database_url, row_factory=dict_row) as connection:
            action = connection.execute("SELECT * FROM action_proposals WHERE id = %s FOR UPDATE", (action_id,)).fetchone()
            if action is None:
                raise ValueError("action proposal not found")
            self._check_version(connection, action["incident_id"], expected_version)
            if action["status"] != "pending_approval":
                return self._action(action)
            if action["approval_expires_at"] < now:
                connection.execute("UPDATE action_proposals SET status = 'expired', updated_at = %s WHERE id = %s", (now, action_id))
                raise ValueError("action approval expired")
            status = "approved" if approved else "rejected"
            connection.execute(
                "UPDATE action_proposals SET status = %s, approved_by = %s, updated_at = %s WHERE id = %s",
                (status, responder, now, action_id),
            )
            self._timeline(connection, action["incident_id"], "action_decision", {"action_id": str(action_id), "status": status, "approved_by": responder})
            return self._get_action(connection, action_id)

    @staticmethod
    def _check_version(connection: Any, incident_id: UUID, expected_version: int | None) -> None:
        if expected_version is None:
            return
        incident = connection.execute(
            "SELECT version FROM incidents WHERE id = %s FOR UPDATE", (incident_id,)
        ).fetchone()
        if incident is None:
            raise ValueError("incident not found")
        if expected_version != incident["version"]:
            raise ValueError("incident version conflict")

    def execute_action(self, action_id: UUID) -> dict[str, Any]:
        now = datetime.now(timezone.utc)
        with psycopg.connect(self.database_url, row_factory=dict_row) as connection:
            action = connection.execute("SELECT * FROM action_proposals WHERE id = %s FOR UPDATE", (action_id,)).fetchone()
            if action is None:
                raise ValueError("action proposal not found")
            if action["status"] != "approved":
                raise ValueError("action is not approved")
            connection.execute("UPDATE action_proposals SET status = 'running', updated_at = %s WHERE id = %s", (now, action_id))
            try:
                simulator_service.select_scenario(action["scenario_id"])
                result = simulator_service.execute_action(action["action_type"], action["target"], action["parameters"], str(action["idempotency_key"]))
                status = "timed_out" if result["status"] == "timed_out" else "completed"
            except ValueError as error:
                result = {"error": str(error)}
                status = "failed"
            connection.execute(
                "UPDATE action_proposals SET status = %s, simulator_action_id = %s, result = %s, updated_at = %s WHERE id = %s",
                (status, UUID(result["id"]) if result.get("id") else None, Jsonb(result), now, action_id),
            )
            self._timeline(connection, action["incident_id"], "action_result", {"action_id": str(action_id), "status": status})
            return self._get_action(connection, action_id)

    def verify_action(self, action_id: UUID) -> dict[str, Any]:
        with psycopg.connect(self.database_url, row_factory=dict_row) as connection:
            action = connection.execute("SELECT * FROM action_proposals WHERE id = %s FOR UPDATE", (action_id,)).fetchone()
            if action is None:
                raise ValueError("action proposal not found")
            if not action["simulator_action_id"]:
                raise ValueError("action has not executed")
            result = simulator_service.verify_action(action["simulator_action_id"])
            connection.execute("UPDATE action_proposals SET status = 'verified', result = %s, updated_at = %s WHERE id = %s", (Jsonb(result), datetime.now(timezone.utc), action_id))
            self._timeline(connection, action["incident_id"], "action_verified", {"action_id": str(action_id), "verified": True})
            return self._get_action(connection, action_id)

    def reconcile_action(self, action_id: UUID) -> dict[str, Any]:
        with psycopg.connect(self.database_url, row_factory=dict_row) as connection:
            action = connection.execute("SELECT * FROM action_proposals WHERE id = %s FOR UPDATE", (action_id,)).fetchone()
            if action is None:
                raise ValueError("action proposal not found")
            if action["status"] != "unknown":
                return self._action(action)
            result = self.action_executor_gateway.reconcile(action)
            if result is None:
                raise ValueError("action executor is not configured")
            status = result.get("status")
            if status not in {"completed", "failed", "timed_out", "unknown"}:
                raise ValueError("action executor returned an invalid status")
            now = datetime.now(timezone.utc)
            connection.execute(
                "UPDATE action_proposals SET status = %s, result = %s, updated_at = %s WHERE id = %s",
                (status, Jsonb(result), now, action_id),
            )
            self._timeline(connection, action["incident_id"], "action_reconciled", {"action_id": str(action_id), "status": status})
            return self._get_action(connection, action_id)

    @staticmethod
    def _page(row: dict[str, Any]) -> dict[str, Any]:
        return {key: (value.isoformat() if isinstance(value, datetime) else str(value) if isinstance(value, UUID) else value)
                for key, value in row.items()}

    def _get_page(self, connection: Any, page_id: UUID) -> dict[str, Any]:
        return self._page(connection.execute("SELECT * FROM pages WHERE id = %s", (page_id,)).fetchone())

    @staticmethod
    def _action(row: dict[str, Any]) -> dict[str, Any]:
        return {key: (value.isoformat() if isinstance(value, datetime) else str(value) if isinstance(value, UUID) else value)
                for key, value in row.items()}

    def _get_action(self, connection: Any, action_id: UUID) -> dict[str, Any]:
        return self._action(connection.execute("SELECT * FROM action_proposals WHERE id = %s", (action_id,)).fetchone())

    @staticmethod
    def _timeline(connection: Any, incident_id: UUID, event_type: str, payload: dict[str, Any]) -> None:
        connection.execute("SELECT id FROM incidents WHERE id = %s FOR UPDATE", (incident_id,)).fetchone()
        sequence = connection.execute("SELECT COALESCE(MAX(sequence_number), 0) + 1 AS next FROM timeline_events WHERE incident_id = %s", (incident_id,)).fetchone()["next"]
        now = datetime.now(timezone.utc)
        connection.execute(
            """INSERT INTO timeline_events
            (id, incident_id, event_type, event_time, received_time, sequence_number, payload)
            VALUES (%s, %s, %s, %s, %s, %s, %s)""",
            (uuid4(), incident_id, event_type, now, now, sequence, Jsonb(json.loads(json.dumps(payload)))),
        )

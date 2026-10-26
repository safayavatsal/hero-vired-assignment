import json
import os
from datetime import datetime, timezone
from typing import Any
from uuid import UUID, uuid4

import psycopg
from psycopg.rows import dict_row
from psycopg.types.json import Jsonb

from app.domain.incident import Alert, INCIDENT_TRANSITIONS


DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://postgres:postgres@localhost:5432/hero_vired",
)

class PostgresIncidentRepository:
    def __init__(self, database_url: str = DATABASE_URL) -> None:
        self.database_url = database_url

    def accept_alert(self, alert: Alert) -> dict[str, Any]:
        with psycopg.connect(self.database_url, row_factory=dict_row) as connection:
            duplicate = connection.execute(
                """
                SELECT a.id AS alert_id, a.incident_id, i.*
                FROM alerts a JOIN incidents i ON i.id = a.incident_id
                WHERE a.source_event_id = %s
                """,
                (alert.source_event_id,),
            ).fetchone()
            if duplicate:
                return self._response(connection, duplicate["incident_id"], duplicate["alert_id"], True)

            incident = connection.execute(
                "SELECT * FROM incidents WHERE fingerprint = %s FOR UPDATE",
                (alert.fingerprint,),
            ).fetchone()
            correlation_key = alert.raw_payload.get("correlation_key")
            if incident is None and correlation_key:
                incident = connection.execute(
                    """
                    SELECT i.*
                    FROM incidents i
                    JOIN alerts a ON a.incident_id = i.id
                    WHERE a.service = %s
                      AND a.raw_payload->>'correlation_key' = %s
                      AND a.source_time BETWEEN %s - INTERVAL '15 minutes' AND %s + INTERVAL '15 minutes'
                    ORDER BY a.source_time DESC
                    LIMIT 1
                    FOR UPDATE OF i
                    """,
                    (alert.service, str(correlation_key), alert.source_time, alert.source_time),
                ).fetchone()
            if incident is None and not correlation_key:
                incident = connection.execute(
                    """
                    SELECT i.*
                    FROM incidents i
                    JOIN alerts a ON a.incident_id = i.id
                    WHERE a.source_time BETWEEN %s - INTERVAL '15 minutes' AND %s + INTERVAL '15 minutes'
                      AND (
                          a.service = %s
                          OR a.labels->>'dependency' = %s
                          OR a.service = %s
                          OR a.labels->>'dependency' = %s
                      )
                    ORDER BY a.source_time DESC
                    LIMIT 1
                    FOR UPDATE OF i
                    """,
                    (
                        alert.source_time,
                        alert.source_time,
                        alert.service,
                        alert.raw_payload.get("labels", {}).get("dependency"),
                        alert.raw_payload.get("labels", {}).get("dependency"),
                        alert.service,
                    ),
                ).fetchone()
            if incident is None:
                incident = {
                    "id": uuid4(),
                    "fingerprint": alert.fingerprint,
                    "service": alert.service,
                    "severity": alert.severity,
                    "status": "resolved" if alert.lifecycle == "resolved" else "received",
                    "summary": alert.description,
                    "version": 1,
                    "created_at": alert.received_time,
                    "updated_at": alert.received_time,
                }
                connection.execute(
                    """
                    INSERT INTO incidents
                    (id, fingerprint, service, severity, status, summary, version, created_at, updated_at)
                    VALUES (%(id)s, %(fingerprint)s, %(service)s, %(severity)s, %(status)s,
                            %(summary)s, %(version)s, %(created_at)s, %(updated_at)s)
                    """,
                    incident,
                )
            alert.incident_id = incident["id"]
            connection.execute(
                """
                INSERT INTO alerts
                (id, incident_id, source_event_id, fingerprint, source, service, severity,
                 alert_type, labels, description, lifecycle, source_time, received_time, raw_payload)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    alert.id, alert.incident_id, alert.source_event_id, alert.fingerprint,
                    alert.source, alert.service, alert.severity, alert.alert_type,
                    Jsonb(alert.labels), alert.description, alert.lifecycle,
                    alert.source_time, alert.received_time, Jsonb(_json_safe(alert.raw_payload)),
                ),
            )
            latest_alert = connection.execute(
                """
                SELECT lifecycle
                FROM alerts
                WHERE incident_id = %s
                ORDER BY source_time DESC, received_time DESC, id DESC
                LIMIT 1
                """,
                (alert.incident_id,),
            ).fetchone()
            status = incident["status"]
            if latest_alert and latest_alert["lifecycle"] == "resolved":
                status = "resolved"
            elif status == "resolved":
                status = "received"
            connection.execute(
                """
                UPDATE incidents
                SET status = %s, updated_at = %s, version = version + 1
                WHERE id = %s
                """,
                (status, alert.received_time, incident["id"]),
            )
            sequence = connection.execute(
                "SELECT id FROM incidents WHERE id = %s FOR UPDATE",
                (alert.incident_id,),
            ).fetchone()
            sequence = connection.execute(
                "SELECT COALESCE(MAX(sequence_number), 0) + 1 AS next FROM timeline_events WHERE incident_id = %s",
                (alert.incident_id,),
            ).fetchone()["next"]
            connection.execute(
                """
                INSERT INTO timeline_events
                (id, incident_id, event_type, event_time, received_time, sequence_number, payload)
                VALUES (%s, %s, 'alert_received', %s, %s, %s, %s)
                """,
                (
                    uuid4(), alert.incident_id, alert.source_time, alert.received_time, sequence,
                    Jsonb(_json_safe({"alert_id": str(alert.id), "source_event_id": alert.source_event_id,
                                      "fingerprint": alert.fingerprint, "lifecycle": alert.lifecycle,
                                      "raw_payload": alert.raw_payload})),
                ),
            )
            return self._response(connection, alert.incident_id, alert.id, False)

    def list_incidents(self) -> list[dict[str, Any]]:
        with psycopg.connect(self.database_url, row_factory=dict_row) as connection:
            rows = connection.execute(
                """
                SELECT i.*, COUNT(a.id)::int AS alert_count
                FROM incidents i LEFT JOIN alerts a ON a.incident_id = i.id
                GROUP BY i.id ORDER BY i.updated_at DESC
                """
            ).fetchall()
            return [self._summary(row) for row in rows]

    def get_incident(self, incident_id: UUID) -> dict[str, Any] | None:
        with psycopg.connect(self.database_url, row_factory=dict_row) as connection:
            row = connection.execute(
                """
                SELECT i.*, COUNT(a.id)::int AS alert_count
                FROM incidents i LEFT JOIN alerts a ON a.incident_id = i.id
                WHERE i.id = %s GROUP BY i.id
                """, (incident_id,)
            ).fetchone()
            if row is None:
                return None
            result = self._summary(row)
            result["created_at"] = row["created_at"].isoformat()
            result["alerts"] = [self._alert(row) for row in connection.execute(
                "SELECT * FROM alerts WHERE incident_id = %s ORDER BY received_time, id", (incident_id,)
            ).fetchall()]
            result["timeline"] = self._timeline(connection, incident_id)
            return result

    def get_timeline(self, incident_id: UUID) -> list[dict[str, Any]] | None:
        with psycopg.connect(self.database_url, row_factory=dict_row) as connection:
            if connection.execute("SELECT 1 FROM incidents WHERE id = %s", (incident_id,)).fetchone() is None:
                return None
            return self._timeline(connection, incident_id)

    def transition(self, incident_id: UUID, target_status: str, expected_version: int | None) -> dict[str, Any]:
        with psycopg.connect(self.database_url, row_factory=dict_row) as connection:
            incident = connection.execute(
                "SELECT * FROM incidents WHERE id = %s FOR UPDATE", (incident_id,)
            ).fetchone()
            if incident is None:
                raise ValueError("incident not found")
            if target_status not in INCIDENT_TRANSITIONS.get(incident["status"], set()):
                raise ValueError(f"invalid transition from {incident['status']} to {target_status}")
            if expected_version is not None and expected_version != incident["version"]:
                raise ValueError("incident version conflict")
            now = datetime.now(incident["updated_at"].tzinfo)
            next_version = incident["version"] + 1
            connection.execute(
                "UPDATE incidents SET status = %s, version = %s, updated_at = %s WHERE id = %s",
                (target_status, next_version, now, incident_id),
            )
            sequence = connection.execute(
                "SELECT COALESCE(MAX(sequence_number), 0) + 1 AS next FROM timeline_events WHERE incident_id = %s",
                (incident_id,),
            ).fetchone()["next"]
            connection.execute(
                """
                INSERT INTO timeline_events
                (id, incident_id, event_type, event_time, received_time, sequence_number, payload)
                VALUES (%s, %s, 'incident_transition', %s, %s, %s, %s)
                """,
                (
                    uuid4(), incident_id, now, now, sequence,
                    Jsonb({"from": incident["status"], "to": target_status, "version": next_version}),
                ),
            )
            connection.commit()
            result = self.get_incident(incident_id)
            if result is None:
                raise ValueError("incident not found")
            return result

    def append_timeline_event(self, incident_id: UUID, event_type: str, payload: dict[str, Any]) -> None:
        with psycopg.connect(self.database_url, row_factory=dict_row) as connection:
            connection.execute("SELECT id FROM incidents WHERE id = %s FOR UPDATE", (incident_id,)).fetchone()
            sequence = connection.execute(
                "SELECT COALESCE(MAX(sequence_number), 0) + 1 AS next FROM timeline_events WHERE incident_id = %s",
                (incident_id,),
            ).fetchone()["next"]
            now = datetime.now(timezone.utc)
            connection.execute(
                """
                INSERT INTO timeline_events
                (id, incident_id, event_type, event_time, received_time, sequence_number, payload)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                """,
                (uuid4(), incident_id, event_type, now, now, sequence, Jsonb(_json_safe(payload))),
            )
            connection.commit()

    def _response(self, connection: Any, incident_id: UUID, alert_id: UUID, duplicate: bool) -> dict[str, Any]:
        incident = connection.execute(
            """
            SELECT i.*, COUNT(a.id)::int AS alert_count
            FROM incidents i LEFT JOIN alerts a ON a.incident_id = i.id
            WHERE i.id = %s GROUP BY i.id
            """, (incident_id,)
        ).fetchone()
        alert = connection.execute("SELECT * FROM alerts WHERE id = %s", (alert_id,)).fetchone()
        return {"duplicate": duplicate, "alert": self._alert(alert), "incident": self._summary(incident)}

    def _timeline(self, connection: Any, incident_id: UUID) -> list[dict[str, Any]]:
        rows = connection.execute(
            """
            SELECT * FROM timeline_events WHERE incident_id = %s
            ORDER BY event_time, received_time, sequence_number
            """, (incident_id,)
        ).fetchall()
        return [{
            "id": str(row["id"]), "incident_id": str(row["incident_id"]),
            "event_type": row["event_type"], "event_time": row["event_time"].isoformat(),
            "received_time": row["received_time"].isoformat(),
            "sequence_number": row["sequence_number"], "payload": row["payload"],
        } for row in rows]

    @staticmethod
    def _summary(row: dict[str, Any]) -> dict[str, Any]:
        return {
            "id": str(row["id"]), "fingerprint": row["fingerprint"], "service": row["service"],
            "severity": row["severity"], "status": row["status"], "summary": row["summary"],
            "version": row["version"], "alert_count": row.get("alert_count", 0),
            "updated_at": row["updated_at"].isoformat(),
        }

    @staticmethod
    def _alert(row: dict[str, Any]) -> dict[str, Any]:
        return {
            "id": str(row["id"]), "incident_id": str(row["incident_id"]),
            "source_event_id": row["source_event_id"], "fingerprint": row["fingerprint"],
            "source": row["source"], "service": row["service"], "severity": row["severity"],
            "alert_type": row["alert_type"], "labels": row["labels"], "description": row["description"],
            "lifecycle": row["lifecycle"], "source_time": row["source_time"].isoformat(),
            "received_time": row["received_time"].isoformat(), "raw_payload": row["raw_payload"],
        }


def _json_safe(value: Any) -> Any:
    return json.loads(json.dumps(value, default=lambda item: item.isoformat() if isinstance(item, datetime) else str(item)))

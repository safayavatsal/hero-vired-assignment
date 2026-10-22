import json
import os
from datetime import datetime
from typing import Any
from uuid import UUID, uuid4

import psycopg
from psycopg.rows import dict_row
from psycopg.types.json import Jsonb


DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://postgres:postgres@localhost:5432/oncall",
)

SCHEMA = """
CREATE TABLE IF NOT EXISTS investigations (
    id UUID PRIMARY KEY,
    incident_id UUID NOT NULL REFERENCES incidents(id),
    scenario_id TEXT NOT NULL,
    generated_at TIMESTAMPTZ NOT NULL,
    model_status TEXT NOT NULL,
    model_error TEXT,
    model_analysis JSONB,
    prompt_version TEXT NOT NULL DEFAULT 'investigation-v1',
    UNIQUE (incident_id)
);
ALTER TABLE investigations ADD COLUMN IF NOT EXISTS model_error TEXT;
ALTER TABLE investigations ADD COLUMN IF NOT EXISTS model_analysis JSONB;
ALTER TABLE investigations ADD COLUMN IF NOT EXISTS prompt_version TEXT NOT NULL DEFAULT 'investigation-v1';
CREATE TABLE IF NOT EXISTS investigation_evidence (
    id TEXT NOT NULL,
    investigation_id UUID NOT NULL REFERENCES investigations(id) ON DELETE CASCADE,
    source_type TEXT NOT NULL,
    availability TEXT NOT NULL,
    observed_at TIMESTAMPTZ NOT NULL,
    items JSONB NOT NULL,
    PRIMARY KEY (investigation_id, id)
);
CREATE TABLE IF NOT EXISTS investigation_findings (
    id TEXT NOT NULL,
    investigation_id UUID NOT NULL REFERENCES investigations(id) ON DELETE CASCADE,
    category TEXT NOT NULL,
    statement TEXT NOT NULL,
    confidence DOUBLE PRECISION NOT NULL,
    suggested_next_step TEXT NOT NULL,
    evidence_ids JSONB NOT NULL,
    uncertainty TEXT,
    PRIMARY KEY (investigation_id, id)
);
"""


class PostgresInvestigationRepository:
    def __init__(self, database_url: str = DATABASE_URL) -> None:
        self.database_url = database_url

    def initialize(self) -> None:
        with psycopg.connect(self.database_url) as connection:
            connection.execute(SCHEMA)

    def save(self, result: dict[str, Any]) -> None:
        investigation_id = uuid4()
        with psycopg.connect(self.database_url) as connection:
            existing = connection.execute(
                "SELECT id FROM investigations WHERE incident_id = %s",
                (UUID(result["incident_id"]),),
            ).fetchone()
            if existing:
                investigation_id = existing[0]
                connection.execute("DELETE FROM investigations WHERE id = %s", (investigation_id,))
            connection.execute(
                """
                INSERT INTO investigations
                (id, incident_id, scenario_id, generated_at, model_status, model_error, model_analysis, prompt_version)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    investigation_id,
                    UUID(result["incident_id"]),
                    result["scenario_id"],
                    datetime.fromisoformat(result["generated_at"]),
                    result["model_status"], result.get("model_error"),
                    Jsonb(_json_safe(result["model_analysis"])) if result.get("model_analysis") else None,
                    result.get("prompt_version", "investigation-v1"),
                ),
            )
            for evidence in result["evidence"]:
                connection.execute(
                    """
                    INSERT INTO investigation_evidence
                    (id, investigation_id, source_type, availability, observed_at, items)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    """,
                    (
                        evidence["id"], investigation_id, evidence["source_type"],
                        evidence["availability"], datetime.fromisoformat(evidence["observed_at"]),
                        Jsonb(_json_safe(evidence["items"])),
                    ),
                )
            for finding in result["findings"]:
                connection.execute(
                    """
                    INSERT INTO investigation_findings
                    (id, investigation_id, category, statement, confidence,
                     suggested_next_step, evidence_ids, uncertainty)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    """,
                    (
                        finding["id"], investigation_id, finding["category"], finding["statement"],
                        finding["confidence"], finding["suggested_next_step"],
                        Jsonb(finding["evidence_ids"]), finding["uncertainty"],
                    ),
                )

    def get(self, incident_id: UUID) -> dict[str, Any] | None:
        with psycopg.connect(self.database_url, row_factory=dict_row) as connection:
            investigation = connection.execute(
                "SELECT * FROM investigations WHERE incident_id = %s",
                (incident_id,),
            ).fetchone()
            if investigation is None:
                return None
            evidence = connection.execute(
                "SELECT * FROM investigation_evidence WHERE investigation_id = %s ORDER BY source_type",
                (investigation["id"],),
            ).fetchall()
            findings = connection.execute(
                "SELECT * FROM investigation_findings WHERE investigation_id = %s ORDER BY id",
                (investigation["id"],),
            ).fetchall()
            return {
                "incident_id": str(incident_id),
                "scenario_id": investigation["scenario_id"],
                "generated_at": investigation["generated_at"].isoformat(),
                "model_status": investigation["model_status"],
                "model_error": investigation["model_error"],
                "model_analysis": investigation["model_analysis"],
                "prompt_version": investigation["prompt_version"],
                "evidence": [{
                    "id": row["id"], "source_type": row["source_type"],
                    "availability": row["availability"], "observed_at": row["observed_at"].isoformat(),
                    "items": row["items"],
                } for row in evidence],
                "findings": [{
                    "id": row["id"], "category": row["category"], "statement": row["statement"],
                    "confidence": row["confidence"], "suggested_next_step": row["suggested_next_step"],
                    "evidence_ids": row["evidence_ids"], "uncertainty": row["uncertainty"],
                } for row in findings],
            }


def _json_safe(value: Any) -> Any:
    return json.loads(json.dumps(value, default=lambda item: item.isoformat() if isinstance(item, datetime) else str(item)))

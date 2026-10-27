import os
from datetime import datetime
from typing import Any
from uuid import UUID, uuid4

import psycopg
from psycopg.rows import dict_row
from psycopg.types.json import Jsonb

from app.application.serialization import json_safe


DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://postgres:postgres@localhost:5432/hero_vired",
)

class PostgresInvestigationRepository:
    def __init__(self, database_url: str = DATABASE_URL) -> None:
        self.database_url = database_url

    def save(self, result: dict[str, Any]) -> UUID:
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
                (id, incident_id, scenario_id, generated_at, model_status, model_error, model_analysis, prompt_version, tool_trace, model_telemetry)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    investigation_id,
                    UUID(result["incident_id"]),
                    result["scenario_id"],
                    datetime.fromisoformat(result["generated_at"]),
                    result["model_status"], result.get("model_error"),
                    Jsonb(json_safe(result["model_analysis"])) if result.get("model_analysis") else None,
                    result.get("prompt_version", "investigation-v1"),
                    Jsonb(json_safe(result.get("tool_trace", []))),
                    Jsonb(json_safe(result.get("model_telemetry", {}))),
                ),
            )
            for evidence in result["evidence"]:
                connection.execute(
                    """
                    INSERT INTO investigation_evidence
                    (id, investigation_id, source_type, query, parameters, availability, observed_at, collected_at, duration_ms, error, items)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """,
                    (
                        evidence["id"], investigation_id, evidence["source_type"],
                        evidence.get("query", ""), Jsonb(json_safe(evidence.get("parameters") or {})),
                        evidence["availability"], datetime.fromisoformat(evidence["observed_at"]),
                        datetime.fromisoformat(result["generated_at"]), evidence.get("duration_ms"), evidence.get("error"),
                        Jsonb(json_safe(evidence["items"])),
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
        return investigation_id

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
                "status": "completed",
                "generated_at": investigation["generated_at"].isoformat(),
                "model_status": investigation["model_status"],
                "model_error": investigation["model_error"],
                "model_analysis": investigation["model_analysis"],
                "tool_trace": investigation["tool_trace"],
                "model_telemetry": investigation["model_telemetry"],
                "prompt_version": investigation["prompt_version"],
                "prompt_contract_hash": prompt_contract_hash(),
                "evidence": [{
                    "id": row["id"], "source_type": row["source_type"],
                    "query": row["query"], "parameters": row["parameters"],
                    "availability": row["availability"], "observed_at": row["observed_at"].isoformat(),
                    "collected_at": row["collected_at"].isoformat(), "duration_ms": row["duration_ms"],
                    "error": row["error"], "items": row["items"],
                } for row in evidence],
                "findings": [{
                    "id": row["id"], "category": row["category"], "statement": row["statement"],
                    "confidence": row["confidence"], "suggested_next_step": row["suggested_next_step"],
                    "evidence_ids": row["evidence_ids"], "uncertainty": row["uncertainty"],
                } for row in findings],
            }

def prompt_contract_hash() -> str:
    from app.application.investigation import InvestigationService

    return InvestigationService.PROMPT_CONTRACT_HASH

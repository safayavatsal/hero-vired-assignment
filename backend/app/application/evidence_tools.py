from dataclasses import dataclass
from typing import Any, Protocol


class EvidenceQueryProvider(Protocol):
    def query_evidence(self, source_type: str) -> dict[str, Any]: ...


@dataclass(frozen=True)
class EvidenceTool:
    source_type: str
    name: str
    purpose: str
    enabled: bool = True

    def query(self, provider: EvidenceQueryProvider) -> dict[str, Any]:
        return provider.query_evidence(self.source_type)


EVIDENCE_TOOLS = (
    EvidenceTool("logs", "simulator.evidence.logs", "Inspect recent error and warning events."),
    EvidenceTool("metrics", "simulator.evidence.metrics", "Compare observed values with alert thresholds."),
    EvidenceTool("deploys", "simulator.evidence.deploys", "Check recent versions and deployment changes."),
    EvidenceTool("service_health", "simulator.evidence.service_health", "Confirm local and dependency health."),
)

SIMILAR_INCIDENTS_TOOL = EvidenceTool(
    "similar_incidents",
    "similar_incidents",
    "Find ranked findings from completed incidents with related service and symptoms.",
)


def evidence_tool_catalog(include_similar: bool = True) -> list[dict[str, Any]]:
    tools = EVIDENCE_TOOLS + ((SIMILAR_INCIDENTS_TOOL,) if include_similar else ())
    return [
        {
            "source_type": tool.source_type,
            "name": tool.name,
            "purpose": tool.purpose,
            "enabled": tool.enabled,
        }
        for tool in tools
    ]

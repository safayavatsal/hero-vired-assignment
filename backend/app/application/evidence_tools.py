from dataclasses import dataclass
from typing import Any, Protocol


class EvidenceQueryProvider(Protocol):
    def query_evidence(self, source_type: str) -> dict[str, Any]: ...


@dataclass(frozen=True)
class EvidenceTool:
    source_type: str
    name: str

    def query(self, provider: EvidenceQueryProvider) -> dict[str, Any]:
        return provider.query_evidence(self.source_type)


EVIDENCE_TOOLS = tuple(
    EvidenceTool(source_type, f"simulator.evidence.{source_type}")
    for source_type in ("logs", "metrics", "deploys", "service_health")
)

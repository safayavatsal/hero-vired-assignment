from dataclasses import asdict, dataclass
import hashlib
from typing import Any, Protocol


@dataclass(frozen=True)
class AnalyzerFinding:
    analyzer: str
    kind: str
    name: str
    namespace: str | None
    severity: str
    reason: str
    evidence: dict[str, Any]
    suggested_next_step: str

    def as_dict(self) -> dict[str, Any]:
        value = asdict(self)
        value["id"] = hashlib.sha256(
            f"{self.analyzer}:{self.kind}:{self.namespace}:{self.name}:{self.reason}".encode()
        ).hexdigest()[:16]
        return value


class ResourceAnalyzer(Protocol):
    name: str
    resource_types: tuple[str, ...]

    def analyze(self, resources: list[dict[str, Any]]) -> list[AnalyzerFinding]: ...


def _metadata(resource: dict[str, Any]) -> dict[str, Any]:
    value = resource.get("metadata", {})
    return value if isinstance(value, dict) else {}


def _kind(resource: dict[str, Any]) -> str:
    return str(resource.get("kind", "")).strip()


def _reference(resource: dict[str, Any]) -> tuple[str, str, str | None]:
    metadata = _metadata(resource)
    return _kind(resource), str(metadata.get("name", "unknown")), metadata.get("namespace")


def _finding(resource: dict[str, Any], analyzer: str, reason: str, evidence: dict[str, Any], *, severity: str = "warning", next_step: str = "inspect") -> AnalyzerFinding:
    kind, name, namespace = _reference(resource)
    return AnalyzerFinding(analyzer, kind, name, namespace, severity, reason, evidence, next_step)


class PodAnalyzer:
    name = "pod"
    resource_types = ("Pod",)
    _waiting_reasons = {"CrashLoopBackOff", "ImagePullBackOff", "ErrImagePull", "CreateContainerConfigError", "CreateContainerError"}

    def analyze(self, resources: list[dict[str, Any]]) -> list[AnalyzerFinding]:
        findings: list[AnalyzerFinding] = []
        for resource in resources:
            status = resource.get("status", {})
            phase = status.get("phase")
            if phase in {"Pending", "Failed", "Unknown"}:
                findings.append(_finding(resource, self.name, f"Pod is in {phase} phase.", {"phase": phase}, next_step="inspect_events"))
            for field in ("initContainerStatuses", "containerStatuses"):
                for container in status.get(field, []) or []:
                    waiting = (container.get("state") or {}).get("waiting") or {}
                    terminated = (container.get("state") or {}).get("terminated") or {}
                    reason = waiting.get("reason")
                    if reason in self._waiting_reasons:
                        findings.append(_finding(resource, self.name, f"Container {container.get('name', 'unknown')} is {reason}.", {"container": container.get("name"), "reason": reason, "message": waiting.get("message")}, next_step="inspect_events"))
                    elif terminated and terminated.get("exitCode", 0) != 0:
                        findings.append(_finding(resource, self.name, f"Container {container.get('name', 'unknown')} terminated with exit code {terminated.get('exitCode')}.", {"container": container.get("name"), "exit_code": terminated.get("exitCode"), "reason": terminated.get("reason")}, next_step="inspect_logs"))
                    elif container.get("ready") is False and phase == "Running":
                        findings.append(_finding(resource, self.name, f"Container {container.get('name', 'unknown')} is not ready.", {"container": container.get("name"), "ready": False}, next_step="inspect_events"))
        return findings


class DeploymentAnalyzer:
    name = "deployment"
    resource_types = ("Deployment",)

    def analyze(self, resources: list[dict[str, Any]]) -> list[AnalyzerFinding]:
        findings: list[AnalyzerFinding] = []
        for resource in resources:
            spec = resource.get("spec", {})
            status = resource.get("status", {})
            desired = int(spec.get("replicas", 1))
            ready = int(status.get("readyReplicas", 0))
            conditions = status.get("conditions", []) or []
            progressing = any(item.get("type") == "Progressing" and item.get("status") == "True" for item in conditions)
            if desired != ready and not progressing:
                findings.append(_finding(resource, self.name, f"Deployment has {desired} desired replicas but {ready} ready replicas.", {"desired": desired, "ready": ready, "available": status.get("availableReplicas", 0)}, next_step="inspect_pods"))
            for condition in conditions:
                if condition.get("type") == "Progressing" and condition.get("status") == "False":
                    findings.append(_finding(resource, self.name, f"Deployment progression failed: {condition.get('reason', 'unknown reason')}.", {"reason": condition.get("reason"), "message": condition.get("message")}, next_step="inspect_events"))
        return findings


class ServiceAnalyzer:
    name = "service"
    resource_types = ("Service",)

    def analyze(self, resources: list[dict[str, Any]]) -> list[AnalyzerFinding]:
        findings: list[AnalyzerFinding] = []
        for resource in resources:
            spec = resource.get("spec", {})
            status = resource.get("status", {})
            if not spec.get("selector") and spec.get("type") != "ExternalName":
                findings.append(_finding(resource, self.name, "Service has no selector and may not route to workload endpoints.", {"selector": spec.get("selector")}, next_step="inspect_endpoints"))
            endpoints = status.get("endpoints")
            if isinstance(endpoints, list) and not endpoints:
                findings.append(_finding(resource, self.name, "Service has no ready endpoints.", {"endpoints": []}, next_step="inspect_pods"))
        return findings


class EventAnalyzer:
    name = "event"
    resource_types = ("Event", "Events")

    def analyze(self, resources: list[dict[str, Any]]) -> list[AnalyzerFinding]:
        return [
            _finding(resource, self.name, f"Warning event: {resource.get('reason', 'unknown reason')}.", {"reason": resource.get("reason"), "message": resource.get("message"), "type": resource.get("type")}, next_step="inspect_related_resource")
            for resource in resources
            if resource.get("type", "Warning") == "Warning"
        ]


class NodeAnalyzer:
    name = "node"
    resource_types = ("Node",)
    _pressure_types = {"MemoryPressure", "DiskPressure", "PIDPressure", "NetworkUnavailable"}

    def analyze(self, resources: list[dict[str, Any]]) -> list[AnalyzerFinding]:
        findings: list[AnalyzerFinding] = []
        for resource in resources:
            for condition in resource.get("status", {}).get("conditions", []) or []:
                if condition.get("type") == "Ready" and condition.get("status") != "True":
                    findings.append(_finding(resource, self.name, f"Node is not ready: {condition.get('reason', 'unknown reason')}.", {"condition": condition.get("type"), "status": condition.get("status"), "message": condition.get("message")}, severity="critical", next_step="inspect_node_events"))
                elif condition.get("type") in self._pressure_types and condition.get("status") == "True":
                    findings.append(_finding(resource, self.name, f"Node reports {condition.get('type')}.", {"condition": condition.get("type"), "status": condition.get("status"), "message": condition.get("message")}, severity="critical", next_step="inspect_node_capacity"))
        return findings


class PersistentVolumeClaimAnalyzer:
    name = "persistent_volume_claim"
    resource_types = ("PersistentVolumeClaim",)

    def analyze(self, resources: list[dict[str, Any]]) -> list[AnalyzerFinding]:
        return [
            _finding(resource, self.name, f"PersistentVolumeClaim is {phase}, not Bound.", {"phase": phase}, next_step="inspect_storage")
            for resource in resources
            if (phase := resource.get("status", {}).get("phase", "Unknown")) != "Bound"
        ]


ANALYZERS: tuple[ResourceAnalyzer, ...] = (
    PodAnalyzer(),
    DeploymentAnalyzer(),
    ServiceAnalyzer(),
    EventAnalyzer(),
    NodeAnalyzer(),
    PersistentVolumeClaimAnalyzer(),
)


def analyzer_catalog() -> list[dict[str, Any]]:
    return [{"name": analyzer.name, "resource_types": list(analyzer.resource_types), "read_only": True} for analyzer in ANALYZERS]


def _matches(resource: dict[str, Any], namespace: str | None, resource_type: str | None, resource_name: str | None, labels: dict[str, str]) -> bool:
    metadata = _metadata(resource)
    if namespace and metadata.get("namespace") != namespace:
        return False
    if resource_type and _kind(resource).lower() != resource_type.lower():
        return False
    if resource_name and metadata.get("name") != resource_name:
        return False
    resource_labels = metadata.get("labels", {})
    return all(resource_labels.get(key) == value for key, value in labels.items())


def analyze_resources(resources: list[dict[str, Any]], *, namespace: str | None = None, resource_type: str | None = None, resource_name: str | None = None, labels: dict[str, str] | None = None, analyzer_names: list[str] | None = None) -> dict[str, Any]:
    selected = list(ANALYZERS)
    if analyzer_names is not None:
        available = {analyzer.name: analyzer for analyzer in ANALYZERS}
        unknown = sorted(set(analyzer_names) - set(available))
        if unknown:
            raise ValueError(f"unknown analyzer: {unknown[0]}")
        selected = [available[name] for name in analyzer_names]
    filtered = [resource for resource in resources if isinstance(resource, dict) and _matches(resource, namespace, resource_type, resource_name, labels or {})]
    findings: list[dict[str, Any]] = []
    for analyzer in selected:
        scoped = [resource for resource in filtered if _kind(resource) in analyzer.resource_types]
        findings.extend(item.as_dict() for item in analyzer.analyze(scoped))
    return {
        "status": "problem_detected" if findings else "ok",
        "problems": len(findings),
        "resources_scanned": len(filtered),
        "filters": {"namespace": namespace, "resource_type": resource_type, "resource_name": resource_name, "labels": labels or {}},
        "analyzers": analyzer_catalog(),
        "findings": findings,
        "errors": [],
    }

import os
import re
import json
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen
from typing import Any, Protocol

class ModelUnavailableError(Exception):
    pass


class ModelRateLimitError(Exception):
    pass


class ModelGateway(Protocol):
    def analyze(self, prompt: dict[str, Any]) -> dict[str, Any]: ...


class UnavailableModelGateway:
    def analyze(self, prompt: dict[str, Any]) -> dict[str, Any]:
        raise ModelUnavailableError("model gateway is not configured")


class HttpModelGateway:
    def __init__(self, url: str, token: str, timeout_seconds: float = 5.0) -> None:
        self.url = url
        self.token = token
        self.timeout_seconds = timeout_seconds

    def analyze(self, prompt: dict[str, Any]) -> dict[str, Any]:
        request = Request(
            self.url,
            data=json.dumps(prompt).encode("utf-8"),
            headers={"Authorization": f"Bearer {self.token}", "Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urlopen(request, timeout=self.timeout_seconds) as response:
                if response.status == 429:
                    raise ModelRateLimitError("model gateway rate limited the request")
                result = json.loads(response.read())
        except HTTPError as error:
            if error.code == 429:
                raise ModelRateLimitError("model gateway rate limited the request") from error
            raise ValueError(f"model gateway returned HTTP {error.code}") from error
        except URLError as error:
            raise ModelUnavailableError("model gateway is unavailable") from error
        if not isinstance(result, dict):
            raise ValueError("model response must be an object")
        return result


def configured_model_gateway() -> ModelGateway:
    url = os.getenv("MODEL_GATEWAY_URL")
    token = os.getenv("MODEL_GATEWAY_TOKEN")
    if not url or not token:
        return UnavailableModelGateway()
    return HttpModelGateway(url, token)


def mask_sensitive(value: Any) -> Any:
    if isinstance(value, dict):
        return {key: "[REDACTED]" if _sensitive_key(key) else mask_sensitive(item) for key, item in value.items()}
    if isinstance(value, list):
        return [mask_sensitive(item) for item in value]
    if isinstance(value, str):
        value = re.sub(r"(?i)(bearer\s+)[A-Za-z0-9._-]+", r"\1[REDACTED]", value)
        return re.sub(r"(?i)(token|secret|password|api[_-]?key)\s*[:=]\s*[^\s,;]+", r"\1=[REDACTED]", value)
    return value


def _sensitive_key(key: str) -> bool:
    normalized = key.lower().replace("-", "_")
    return any(part in normalized for part in ("token", "secret", "password", "api_key"))


def validate_model_response(response: dict[str, Any], evidence_ids: set[str]) -> dict[str, Any]:
    required = {"current_condition", "likely_cause", "confidence", "suggested_next_step", "evidence_ids", "uncertainty"}
    if set(response) < required:
        raise ValueError("model response is missing required fields")
    if not isinstance(response["confidence"], (int, float)) or not 0 <= response["confidence"] <= 1:
        raise ValueError("model confidence must be between 0 and 1")
    if not isinstance(response["evidence_ids"], list) or not set(response["evidence_ids"]).issubset(evidence_ids):
        raise ValueError("model response cited unsupported evidence")
    return response

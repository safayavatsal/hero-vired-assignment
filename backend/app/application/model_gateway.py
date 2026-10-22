import os
import re
import json
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen
from typing import Any, Protocol

DEFAULT_MODEL_GATEWAY_URL = "https://api.groq.com/openai/v1/responses"


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
    def __init__(self, url: str, token: str, timeout_seconds: float = 5.0, model: str | None = None,
                 response_format: str = "structured") -> None:
        self.url = url
        self.token = token
        self.timeout_seconds = timeout_seconds
        self.model = model
        self.response_format = response_format

    def analyze(self, prompt: dict[str, Any]) -> dict[str, Any]:
        payload = _openai_request(prompt, self.model) if self.response_format == "openai_responses" else prompt
        request = Request(
            self.url,
            data=json.dumps(payload).encode("utf-8"),
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
        if self.response_format == "openai_responses":
            return _openai_response(result)
        if not isinstance(result, dict):
            raise ValueError("model response must be an object")
        return result


def configured_model_gateway() -> ModelGateway:
    url = os.getenv("MODEL_GATEWAY_URL") or DEFAULT_MODEL_GATEWAY_URL
    token = os.getenv("MODEL_GATEWAY_TOKEN")
    if not url or not token:
        return UnavailableModelGateway()
    return HttpModelGateway(
        url,
        token,
        model=os.getenv("MODEL_GATEWAY_MODEL", "openai/gpt-oss-20b"),
        response_format=os.getenv("MODEL_GATEWAY_FORMAT", "structured"),
    )


def _openai_request(prompt: dict[str, Any], model: str | None) -> dict[str, Any]:
    if not model:
        raise ValueError("MODEL_GATEWAY_MODEL is required for openai_responses")
    schema = {
        "type": "object",
        "properties": {
            "current_condition": {"type": "string"},
            "likely_cause": {"type": "string"},
            "confidence": {"type": "number", "minimum": 0, "maximum": 1},
            "suggested_next_step": {"type": "string"},
            "evidence_ids": {"type": "array", "items": {"type": "string"}},
            "uncertainty": {"type": ["string", "null"]},
        },
        "required": ["current_condition", "likely_cause", "confidence", "suggested_next_step", "evidence_ids", "uncertainty"],
        "additionalProperties": False,
    }
    return {
        "model": model,
        "store": False,
        "input": [{"role": "user", "content": [{"type": "input_text", "text": json.dumps(prompt)}]}],
        "text": {"format": {"type": "json_schema", "name": "investigation", "strict": True, "schema": schema}},
    }


def _openai_response(response: dict[str, Any]) -> dict[str, Any]:
    output_text = response.get("output_text")
    if not output_text:
        for item in response.get("output", []):
            for content in item.get("content", []):
                if content.get("type") == "output_text":
                    output_text = content.get("text")
                    break
            if output_text:
                break
    if not isinstance(output_text, str):
        raise ValueError("provider response did not contain structured output")
    try:
        result = json.loads(output_text)
    except json.JSONDecodeError as error:
        raise ValueError("provider structured output was not valid JSON") from error
    if not isinstance(result, dict):
        raise ValueError("provider structured output must be an object")
    return result


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

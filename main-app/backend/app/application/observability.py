import contextvars
import json
import logging
import re
import threading
import uuid
from collections import defaultdict, deque
from time import monotonic
from typing import Any

from starlette.requests import Request


_request_id = contextvars.ContextVar("request_id", default=None)
_REQUEST_ID = re.compile(r"^[A-Za-z0-9._:-]{1,128}$")
_UUID_SEGMENT = re.compile(r"/[0-9a-fA-F-]{36}(?=/|$)")
_NUMBER_SEGMENT = re.compile(r"/\d+(?=/|$)")
logger = logging.getLogger("app.http")


class RuntimeMetrics:
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._counts: defaultdict[tuple[str, str, str], int] = defaultdict(int)
        self._durations: defaultdict[tuple[str, str], deque[float]] = defaultdict(lambda: deque(maxlen=256))

    def record(self, method: str, route: str, status_code: int, duration_ms: float) -> None:
        status_class = f"{status_code // 100}xx"
        key = (method, route, status_class)
        with self._lock:
            self._counts[key] += 1
            self._durations[(method, route)].append(max(0.0, duration_ms))

    def snapshot(self) -> dict[str, Any]:
        with self._lock:
            rows = []
            for (method, route, status_class), count in sorted(self._counts.items()):
                samples = sorted(self._durations[(method, route)])
                rows.append({
                    "method": method,
                    "route": route,
                    "status_class": status_class,
                    "request_count": count,
                    "error_count": count if status_class in {"4xx", "5xx"} else 0,
                    "p50_ms": percentile(samples, 0.50),
                    "p95_ms": percentile(samples, 0.95),
                    "max_ms": round(samples[-1], 2) if samples else 0.0,
                })
            return {"service": "api", "routes": rows}

    def reset(self) -> None:
        with self._lock:
            self._counts.clear()
            self._durations.clear()


runtime_metrics = RuntimeMetrics()


def percentile(samples: list[float], fraction: float) -> float:
    if not samples:
        return 0.0
    index = min(len(samples) - 1, max(0, int((len(samples) - 1) * fraction)))
    return round(samples[index], 2)


def request_id_from_header(value: str | None) -> str:
    return value if value and _REQUEST_ID.fullmatch(value) else uuid.uuid4().hex


def current_request_id() -> str | None:
    return _request_id.get()


def route_template(request: Request) -> str:
    route = request.scope.get("route")
    template = getattr(route, "path", None)
    if isinstance(template, str):
        return template
    path = _UUID_SEGMENT.sub("/{id}", request.url.path)
    return _NUMBER_SEGMENT.sub("/{id}", path) or "/"


async def request_context_middleware(request: Request, call_next):
    request_id = request_id_from_header(request.headers.get("x-request-id"))
    token = _request_id.set(request_id)
    started = monotonic()
    try:
        response = await call_next(request)
    except Exception:
        duration_ms = (monotonic() - started) * 1000
        runtime_metrics.record(request.method, route_template(request), 500, duration_ms)
        logger.exception(json.dumps({
            "event": "http_request_failed",
            "request_id": request_id,
            "method": request.method,
            "route": route_template(request),
            "status_class": "5xx",
            "duration_ms": round(duration_ms, 2),
        }, sort_keys=True))
        raise
    else:
        duration_ms = (monotonic() - started) * 1000
        route = route_template(request)
        runtime_metrics.record(request.method, route, response.status_code, duration_ms)
        response.headers["X-Request-ID"] = request_id
        logger.info(json.dumps({
            "event": "http_request",
            "request_id": request_id,
            "method": request.method,
            "route": route,
            "status_class": f"{response.status_code // 100}xx",
            "duration_ms": round(duration_ms, 2),
        }, sort_keys=True))
        return response
    finally:
        _request_id.reset(token)

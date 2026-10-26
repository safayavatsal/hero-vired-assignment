import contextvars
import re
import uuid


_request_id = contextvars.ContextVar("request_id", default=None)
_REQUEST_ID = re.compile(r"^[A-Za-z0-9._:-]{1,128}$")


def request_id_from_header(value: str | None) -> str:
    return value if value and _REQUEST_ID.fullmatch(value) else uuid.uuid4().hex


def current_request_id() -> str | None:
    return _request_id.get()


def set_request_id(value: str):
    return _request_id.set(value)


def reset_request_id(token) -> None:
    _request_id.reset(token)

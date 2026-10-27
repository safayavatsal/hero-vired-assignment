from collections.abc import Callable
from functools import wraps
from typing import ParamSpec, TypeVar

from fastapi import HTTPException


P = ParamSpec("P")
R = TypeVar("R")


StatusCode = int | Callable[[Exception], int]


def map_error(status_code: StatusCode, exception_type: type[Exception] = ValueError) -> Callable[[Callable[P, R]], Callable[P, R]]:
    def decorator(handler: Callable[P, R]) -> Callable[P, R]:
        @wraps(handler)
        def wrapped(*args: P.args, **kwargs: P.kwargs) -> R:
            try:
                return handler(*args, **kwargs)
            except exception_type as error:
                code = status_code(error) if callable(status_code) else status_code
                raise HTTPException(status_code=code, detail=str(error)) from error

        return wrapped

    return decorator

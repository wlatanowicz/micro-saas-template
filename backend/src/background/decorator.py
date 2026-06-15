from __future__ import annotations

from collections.abc import Callable
from functools import wraps
from typing import Any, TypeVar

from src.background.enqueue import enqueue_task
from src.background.registry import TASK_REGISTRY, RegisteredTask

_F = TypeVar("_F", bound=Callable[..., Any])


def task(*, queue: str) -> Callable[[_F], _F]:
    def decorator(func: _F) -> _F:
        function_path = f"{func.__module__}.{func.__qualname__}"
        registered = RegisteredTask(
            function_path=function_path,
            function=func,
            queue=queue,
        )
        TASK_REGISTRY[function_path] = registered

        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            return func(*args, **kwargs)

        wrapper.enqueue = lambda *args, **kwargs: enqueue_task(registered, *args, **kwargs)  # type: ignore[attr-defined]

        return wrapper  # type: ignore[return-value]

    return decorator

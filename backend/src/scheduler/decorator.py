from __future__ import annotations

from collections.abc import Callable
from datetime import timedelta
from functools import wraps
from typing import Any, TypeVar

from cron_converter import Cron

from src.scheduler.enqueue import enqueue_task
from src.scheduler.registry import TASK_REGISTRY, RegisteredTask
from src.scheduler.validation import validate_schedulable_signature, validate_schedule_options

_F = TypeVar("_F", bound=Callable[..., Any])


def task(
    *,
    queue: str,
    crontab: str | Cron | None = None,
    interval: timedelta | None = None,
    expire: timedelta | None = None,
) -> Callable[[_F], _F]:
    parsed_crontab, parsed_interval = validate_schedule_options(
        crontab=crontab,
        interval=interval,
    )

    def decorator(func: _F) -> _F:
        if parsed_crontab is not None or parsed_interval is not None:
            validate_schedulable_signature(func)

        function_path = f"{func.__module__}.{func.__qualname__}"
        registered = RegisteredTask(
            function_path=function_path,
            function=func,
            queue=queue,
            crontab=parsed_crontab,
            interval=parsed_interval,
            expire=expire,
        )
        TASK_REGISTRY[function_path] = registered

        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            return func(*args, **kwargs)

        wrapper.enqueue = lambda *args, **kwargs: enqueue_task(registered, *args, **kwargs)  # type: ignore[attr-defined]

        return wrapper  # type: ignore[return-value]

    return decorator

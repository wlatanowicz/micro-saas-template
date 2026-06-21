from __future__ import annotations

from collections.abc import Callable, Iterator
from dataclasses import dataclass
from datetime import timedelta
from typing import Any

from cron_converter import Cron

TASK_REGISTRY: dict[str, RegisteredTask] = {}


@dataclass(frozen=True, slots=True)
class RegisteredTask:
    function_path: str
    function: Callable[..., Any]
    queue: str
    crontab: Cron | None = None
    interval: timedelta | None = None
    expire: timedelta | None = None


def iter_scheduled_tasks() -> Iterator[RegisteredTask]:
    for registered in TASK_REGISTRY.values():
        if registered.crontab is not None or registered.interval is not None:
            yield registered

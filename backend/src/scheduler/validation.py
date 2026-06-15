from __future__ import annotations

import inspect
from collections.abc import Callable
from datetime import timedelta
from typing import Any

from cron_converter import Cron


def parse_crontab(crontab: str | Cron | None) -> Cron | None:
    if crontab is None:
        return None
    if isinstance(crontab, str):
        return Cron(crontab)
    return crontab


def validate_schedule_options(
    *,
    crontab: str | Cron | None,
    interval: timedelta | None,
) -> tuple[Cron | None, timedelta | None]:
    if crontab is not None and interval is not None:
        msg = "only one of crontab or interval may be set"
        raise ValueError(msg)
    return parse_crontab(crontab), interval


def validate_schedulable_signature(func: Callable[..., Any]) -> None:
    sig = inspect.signature(func)
    for param in sig.parameters.values():
        if param.kind in (
            inspect.Parameter.VAR_POSITIONAL,
            inspect.Parameter.VAR_KEYWORD,
        ):
            continue
        if param.default is inspect.Parameter.empty:
            msg = (
                f"scheduled task {func.__qualname__!r} has required parameter "
                f"{param.name!r}; all parameters must have defaults"
            )
            raise ValueError(msg)

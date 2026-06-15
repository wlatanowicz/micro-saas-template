from __future__ import annotations

from datetime import timedelta

from src import scheduler

EXECUTIONS: list[tuple[tuple[object, ...], dict[str, object]]] = []
INTERVAL_EXECUTIONS: list[str] = []
CRONTAB_EXECUTIONS: list[str] = []


@scheduler.task(queue="MESSAGES")
def sample_task(value: str, *, flag: bool = False) -> str:
    EXECUTIONS.append(((value,), {"flag": flag}))
    return f"{value}:{flag}"


@scheduler.task(queue="MESSAGES", interval=timedelta(minutes=5))
def interval_sample_task(*, value: str = "default") -> None:
    INTERVAL_EXECUTIONS.append(value)


@scheduler.task(queue="MESSAGES", crontab="0 * * * *")
def crontab_sample_task(*, value: str = "default") -> None:
    CRONTAB_EXECUTIONS.append(value)

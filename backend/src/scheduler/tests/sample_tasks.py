from __future__ import annotations

from src import scheduler

EXECUTIONS: list[tuple[tuple[object, ...], dict[str, object]]] = []


@scheduler.task(queue="MESSAGES")
def sample_task(value: str, *, flag: bool = False) -> str:
    EXECUTIONS.append(((value,), {"flag": flag}))
    return f"{value}:{flag}"

from __future__ import annotations

from src import background

EXECUTIONS: list[tuple[tuple[object, ...], dict[str, object]]] = []


@background.task(queue="MESSAGES")
def sample_task(value: str, *, flag: bool = False) -> str:
    EXECUTIONS.append(((value,), {"flag": flag}))
    return f"{value}:{flag}"

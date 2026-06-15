from __future__ import annotations

from src.scheduler.executor import execute_task
from src.scheduler.tests import sample_tasks


def test_execute_task_imports_and_runs_function() -> None:
    sample_tasks.EXECUTIONS.clear()
    result = execute_task(
        f"{sample_tasks.__name__}.sample_task",
        ["world"],
        {"flag": False},
    )
    assert result == "world:False"
    assert sample_tasks.EXECUTIONS == [(("world",), {"flag": False})]

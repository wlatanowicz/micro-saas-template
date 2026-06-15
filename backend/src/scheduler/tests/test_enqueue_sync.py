from __future__ import annotations

import pytest

from src.scheduler.registry import TASK_REGISTRY
from src.scheduler.tests import sample_tasks
from src.utils.env import ConfigurationError


def test_sync_transport_runs_task_in_process(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("src.scheduler.config.SCHEDULER_TRANSPORT", "sync")
    sample_tasks.EXECUTIONS.clear()
    sample_tasks.sample_task.enqueue("hello", flag=True)
    assert sample_tasks.EXECUTIONS == [(("hello",), {"flag": True})]


def test_sync_transport_rejected_on_lambda(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("src.scheduler.config.SCHEDULER_TRANSPORT", "sync")
    monkeypatch.setenv("AWS_LAMBDA_FUNCTION_NAME", "micro-saas-app-prod-api")
    with pytest.raises(ConfigurationError, match="not supported on AWS Lambda"):
        sample_tasks.sample_task.enqueue("hello")


def test_registered_task_metadata() -> None:
    path = f"{sample_tasks.sample_task.__module__}.{sample_tasks.sample_task.__qualname__}"
    registered = TASK_REGISTRY[path]
    assert registered.queue == "MESSAGES"
    assert registered.function_path == path

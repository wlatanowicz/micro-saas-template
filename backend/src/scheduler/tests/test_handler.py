from __future__ import annotations

import json
from datetime import UTC, datetime
from unittest.mock import patch

import pytest

from src.scheduler.payload import TaskPayload
from src.scheduler.registry import TASK_REGISTRY, RegisteredTask
from src.scheduler_handler import handler


def _sqs_event(*, function_path: str, retry: int = 0) -> dict:
    return {
        "Records": [
            {
                "body": json.dumps(
                    {
                        "function_path": function_path,
                        "args": ["from-sqs"],
                        "kwargs": {"flag": True},
                        "created_at": datetime(2026, 6, 15, 12, 0, tzinfo=UTC).isoformat(),
                        "retry": retry,
                    }
                )
            }
        ]
    }


def test_handler_processes_sqs_records() -> None:
    function_path = "src.scheduler.tests.sample_tasks.sample_task"
    event = _sqs_event(function_path=function_path)
    with patch("src.scheduler_handler.execute_task") as mock_execute:
        result = handler(event, None)
    mock_execute.assert_called_once_with(function_path, ["from-sqs"], {"flag": True})
    assert result == {"processed": 1}


def test_handler_skips_expired_tasks() -> None:
    function_path = "src.scheduler.tests.sample_tasks.sample_task"
    created_at = datetime(2026, 6, 15, 12, 0, tzinfo=UTC)
    event = {
        "Records": [
            {
                "body": json.dumps(
                    {
                        "function_path": function_path,
                        "args": ["from-sqs"],
                        "kwargs": {"flag": True},
                        "created_at": created_at.isoformat(),
                        "expire_seconds": 300.0,
                    }
                )
            }
        ]
    }
    with (
        patch("src.scheduler_handler.execute_task") as mock_execute,
        patch.object(TaskPayload, "is_expired", return_value=True),
    ):
        result = handler(event, None)
    mock_execute.assert_not_called()
    assert result == {"processed": 1}


def test_handler_reenqueues_failed_task_when_retries_remain(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    function_path = "src.scheduler.tests.sample_tasks.sample_task"
    monkeypatch.setitem(
        TASK_REGISTRY,
        function_path,
        RegisteredTask(
            function_path=function_path,
            function=lambda *args, **kwargs: None,
            queue="MESSAGES",
            max_retries=2,
        ),
    )
    event = _sqs_event(function_path=function_path, retry=0)
    with (
        patch("src.scheduler_handler.execute_task", side_effect=RuntimeError("boom")),
        patch("src.scheduler_handler.enqueue_payload") as mock_enqueue,
    ):
        result = handler(event, None)
    mock_enqueue.assert_called_once()
    retry_payload = mock_enqueue.call_args.args[1]
    assert retry_payload.retry == 1
    assert result == {"processed": 1}


def test_handler_does_not_reenqueue_when_retries_exhausted(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    function_path = "src.scheduler.tests.sample_tasks.sample_task"
    monkeypatch.setitem(
        TASK_REGISTRY,
        function_path,
        RegisteredTask(
            function_path=function_path,
            function=lambda *args, **kwargs: None,
            queue="MESSAGES",
            max_retries=2,
        ),
    )
    event = _sqs_event(function_path=function_path, retry=2)
    with (
        patch("src.scheduler_handler.execute_task", side_effect=RuntimeError("boom")),
        patch("src.scheduler_handler.enqueue_payload") as mock_enqueue,
        pytest.raises(RuntimeError, match="boom"),
    ):
        handler(event, None)
    mock_enqueue.assert_not_called()


def test_handler_does_not_reenqueue_when_max_retries_is_zero(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    function_path = "src.scheduler.tests.sample_tasks.sample_task"
    monkeypatch.setitem(
        TASK_REGISTRY,
        function_path,
        RegisteredTask(
            function_path=function_path,
            function=lambda *args, **kwargs: None,
            queue="MESSAGES",
            max_retries=0,
        ),
    )
    event = _sqs_event(function_path=function_path, retry=0)
    with (
        patch("src.scheduler_handler.execute_task", side_effect=RuntimeError("boom")),
        patch("src.scheduler_handler.enqueue_payload") as mock_enqueue,
        pytest.raises(RuntimeError, match="boom"),
    ):
        handler(event, None)
    mock_enqueue.assert_not_called()

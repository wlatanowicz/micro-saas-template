from __future__ import annotations

import json
from datetime import UTC, datetime
from unittest.mock import patch

from src.scheduler.payload import TaskPayload
from src.scheduler_handler import handler


def test_handler_processes_sqs_records() -> None:
    function_path = "src.scheduler.tests.sample_tasks.sample_task"
    event = {
        "Records": [
            {
                "body": json.dumps(
                    {
                        "function_path": function_path,
                        "args": ["from-sqs"],
                        "kwargs": {"flag": True},
                        "created_at": datetime(2026, 6, 15, 12, 0, tzinfo=UTC).isoformat(),
                    }
                )
            }
        ]
    }
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

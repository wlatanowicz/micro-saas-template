from __future__ import annotations

from unittest.mock import patch

from src.cron_handler import handler


def test_cron_handler_bootstraps_registry_and_runs_due_tasks() -> None:
    with (
        patch("src.cron_handler.bootstrap_task_registry") as mock_bootstrap,
        patch("src.cron_handler.run_due_tasks", return_value=["example.task"]) as mock_run,
    ):
        result = handler({}, None)

    mock_bootstrap.assert_called_once_with()
    mock_run.assert_called_once_with()
    assert result == {"enqueued": 1, "tasks": ["example.task"]}

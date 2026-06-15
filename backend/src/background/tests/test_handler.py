from __future__ import annotations

import json
from unittest.mock import patch

from src.background_handler import handler


def test_handler_processes_sqs_records() -> None:
    function_path = "src.background.tests.sample_tasks.sample_task"
    event = {
        "Records": [
            {
                "body": json.dumps(
                    {
                        "function_path": function_path,
                        "args": ["from-sqs"],
                        "kwargs": {"flag": True},
                    }
                )
            }
        ]
    }
    with patch("src.background_handler.execute_task") as mock_execute:
        result = handler(event, None)
    mock_execute.assert_called_once_with(function_path, ["from-sqs"], {"flag": True})
    assert result == {"processed": 1}

from __future__ import annotations

import json
import sys
from unittest.mock import MagicMock

import pytest

from src.scheduler.tests import sample_tasks
from src.utils.env import ConfigurationError


def test_sqs_transport_sends_json_payload(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("src.scheduler.config.SCHEDULER_TRANSPORT", "sqs")
    monkeypatch.setenv("SCHEDULER_QUEUE_MESSAGES_URL", "https://example.com/queue")
    monkeypatch.setenv("AWS_REGION", "eu-central-1")

    mock_client = MagicMock()
    mock_client.send_message.return_value = {"MessageId": "msg-123"}
    mock_boto3 = MagicMock()
    mock_boto3.client.return_value = mock_client
    monkeypatch.setitem(sys.modules, "boto3", mock_boto3)

    message_id = sample_tasks.sample_task.enqueue("hello", flag=True)
    assert message_id == "msg-123"
    mock_boto3.client.assert_called_once_with("sqs", region_name="eu-central-1")
    mock_client.send_message.assert_called_once()
    call_kwargs = mock_client.send_message.call_args.kwargs
    assert call_kwargs["QueueUrl"] == "https://example.com/queue"
    payload = json.loads(call_kwargs["MessageBody"])
    assert payload["function_path"].endswith(".sample_task")
    assert payload["args"] == ["hello"]
    assert payload["kwargs"] == {"flag": True}
    assert "created_at" in payload
    assert payload["retry"] == 0


def test_sqs_transport_requires_queue_url(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("src.scheduler.config.SCHEDULER_TRANSPORT", "sqs")
    monkeypatch.delenv("SCHEDULER_QUEUE_MESSAGES_URL", raising=False)
    with pytest.raises(ConfigurationError, match="SCHEDULER_QUEUE_MESSAGES_URL"):
        sample_tasks.sample_task.enqueue("hello")

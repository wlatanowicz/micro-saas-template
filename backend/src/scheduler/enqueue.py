from __future__ import annotations

import os
from typing import Any

from src.scheduler import config as scheduler_config
from src.scheduler.payload import TaskPayload
from src.scheduler.registry import RegisteredTask
from src.scheduler.sqs import send_message as send_sqs_message
from src.utils.env import ConfigurationError


def enqueue_task(registered: RegisteredTask, *args: Any, **kwargs: Any) -> Any:
    transport = (scheduler_config.SCHEDULER_TRANSPORT or "sync").lower()
    if transport == "sync":
        if os.environ.get("AWS_LAMBDA_FUNCTION_NAME"):
            msg = (
                "SCHEDULER_TRANSPORT=sync is not supported on AWS Lambda; "
                "set SCHEDULER_TRANSPORT=sqs"
            )
            raise ConfigurationError(msg)
        return registered.function(*args, **kwargs)
    if transport == "sqs":
        task_payload = TaskPayload.for_task(registered, *args, **kwargs)
        url = scheduler_config.queue_url(registered.queue)
        return send_sqs_message(queue_url=url, payload=task_payload.to_dict())
    msg = f"unsupported SCHEDULER_TRANSPORT: {transport}"
    raise ConfigurationError(msg)

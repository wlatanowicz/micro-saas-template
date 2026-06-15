from __future__ import annotations

import os
from typing import Any

from src.background import config as background_config
from src.background.registry import RegisteredTask
from src.background.sqs import send_message as send_sqs_message
from src.utils.env import ConfigurationError


def enqueue_task(registered: RegisteredTask, *args: Any, **kwargs: Any) -> Any:
    transport = (background_config.BACKGROUND_TRANSPORT or "sync").lower()
    if transport == "sync":
        if os.environ.get("AWS_LAMBDA_FUNCTION_NAME"):
            msg = (
                "BACKGROUND_TRANSPORT=sync is not supported on AWS Lambda; "
                "set BACKGROUND_TRANSPORT=sqs"
            )
            raise ConfigurationError(msg)
        return registered.function(*args, **kwargs)
    if transport == "sqs":
        payload = {
            "function_path": registered.function_path,
            "args": list(args),
            "kwargs": kwargs,
        }
        url = background_config.queue_url(registered.queue)
        return send_sqs_message(queue_url=url, payload=payload)
    msg = f"unsupported BACKGROUND_TRANSPORT: {transport}"
    raise ConfigurationError(msg)

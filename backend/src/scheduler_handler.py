"""Lambda entrypoint: process scheduled tasks from SQS."""

from __future__ import annotations

import json
import logging
from typing import Any

from src.scheduler.executor import execute_task

logger = logging.getLogger()
logger.setLevel(logging.INFO)


def handler(event: dict[str, Any], context: object) -> dict[str, int]:
    del context
    records = event.get("Records", [])
    processed = 0
    for record in records:
        body = record.get("body")
        if not isinstance(body, str):
            msg = f"SQS record body must be a string, got {type(body).__name__}"
            raise TypeError(msg)
        payload = json.loads(body)
        function_path = payload["function_path"]
        args = payload.get("args", [])
        kwargs = payload.get("kwargs", {})
        if not isinstance(args, list):
            msg = f"payload args must be a list, got {type(args).__name__}"
            raise TypeError(msg)
        if not isinstance(kwargs, dict):
            msg = f"payload kwargs must be a dict, got {type(kwargs).__name__}"
            raise TypeError(msg)
        logger.info("Running scheduled task %s", function_path)
        execute_task(function_path, args, kwargs)
        processed += 1
    return {"processed": processed}

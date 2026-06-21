"""Lambda entrypoint: process scheduled tasks from SQS."""

from __future__ import annotations

import json
import logging
from typing import Any

from src.scheduler.executor import execute_task
from src.scheduler.payload import TaskPayload

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
        payload = TaskPayload.from_dict(json.loads(body))
        if payload.is_expired():
            logger.info("Skipping expired task %s", payload.function_path)
        else:
            logger.info("Running scheduled task %s", payload.function_path)
            execute_task(payload.function_path, payload.args, payload.kwargs)
        processed += 1
    return {"processed": processed}

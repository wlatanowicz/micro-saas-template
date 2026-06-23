"""Lambda entrypoint: process scheduled tasks from SQS."""

from __future__ import annotations

import json
import logging
from typing import Any

from src.scheduler.bootstrap import bootstrap_task_registry
from src.scheduler.enqueue import enqueue_payload
from src.scheduler.executor import execute_task
from src.scheduler.payload import TaskPayload
from src.scheduler.registry import TASK_REGISTRY

logger = logging.getLogger()
logger.setLevel(logging.INFO)


def handler(event: dict[str, Any], context: object) -> dict[str, int]:
    del context
    bootstrap_task_registry()
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
            try:
                execute_task(payload.function_path, payload.args, payload.kwargs)
            except Exception:
                registered = TASK_REGISTRY.get(payload.function_path)
                if registered is None or payload.retry >= registered.max_retries:
                    logger.exception(
                        "Task %s failed (retry=%d, max_retries=%s)",
                        payload.function_path,
                        payload.retry,
                        registered.max_retries if registered is not None else "unknown",
                    )
                    raise
                next_retry = payload.retry + 1
                logger.info(
                    "Re-enqueueing task %s (retry %d/%d)",
                    payload.function_path,
                    next_retry,
                    registered.max_retries,
                )
                enqueue_payload(registered, payload.with_retry(next_retry))
        processed += 1
    return {"processed": processed}

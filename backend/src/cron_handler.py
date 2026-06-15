"""Lambda entrypoint: enqueue due scheduled tasks."""

from __future__ import annotations

import logging
from typing import Any

from src.scheduler.bootstrap import bootstrap_task_registry
from src.scheduler.due import run_due_tasks

logger = logging.getLogger(__name__)


def handler(event: dict[str, Any], context: object) -> dict[str, Any]:
    del event, context
    bootstrap_task_registry()
    enqueued = run_due_tasks()
    logger.info("Enqueued %d due scheduled task(s): %s", len(enqueued), enqueued)
    return {"enqueued": len(enqueued), "tasks": enqueued}

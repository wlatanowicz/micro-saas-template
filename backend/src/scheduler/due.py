from __future__ import annotations

from datetime import datetime, timedelta

from sqlmodel import Session

from src.scheduler.due_checks import is_task_due, utc_now
from src.scheduler.enqueue import enqueue_task
from src.scheduler.models import SchedulerTaskRun
from src.scheduler.registry import iter_scheduled_tasks
from src.utils.db import session_scope


def run_due_tasks(
    *,
    now: datetime | None = None,
    tick_window: timedelta = timedelta(hours=1),
) -> list[str]:
    run_at = now if now is not None else utc_now()
    enqueued: list[str] = []

    with session_scope() as session:
        for registered in iter_scheduled_tasks():
            last_run_at = _get_last_run_at(session, registered.function_path)
            if not is_task_due(
                registered,
                last_run_at=last_run_at,
                now=run_at,
                tick_window=tick_window,
            ):
                continue

            enqueue_task(registered)
            _upsert_last_run(session, registered.function_path, run_at)
            enqueued.append(registered.function_path)

    return enqueued


def _get_last_run_at(session: Session, function_path: str) -> datetime | None:
    record = session.get(SchedulerTaskRun, function_path)
    if record is None:
        return None
    return record.last_run_at


def _upsert_last_run(session: Session, function_path: str, last_run_at: datetime) -> None:
    record = session.get(SchedulerTaskRun, function_path)
    if record is None:
        session.add(SchedulerTaskRun(function_path=function_path, last_run_at=last_run_at))
        return
    record.last_run_at = last_run_at
    session.add(record)

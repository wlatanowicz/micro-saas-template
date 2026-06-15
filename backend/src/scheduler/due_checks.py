from __future__ import annotations

from datetime import UTC, datetime, timedelta

from cron_converter import Cron

from src.scheduler.registry import RegisteredTask


def is_interval_due(
    *,
    interval: timedelta,
    last_run_at: datetime | None,
    now: datetime,
) -> bool:
    if last_run_at is None:
        return True
    return now >= last_run_at + interval


def is_crontab_due(
    *,
    crontab: Cron,
    last_run_at: datetime | None,
    now: datetime,
    tick_window: timedelta,
) -> bool:
    reference = last_run_at if last_run_at is not None else now - tick_window
    schedule = crontab.schedule(reference)
    next_run = schedule.next()
    if last_run_at is not None and next_run <= last_run_at:
        next_run = schedule.next()
    return next_run <= now


def is_task_due(
    registered: RegisteredTask,
    *,
    last_run_at: datetime | None,
    now: datetime,
    tick_window: timedelta,
) -> bool:
    if registered.interval is not None:
        return is_interval_due(interval=registered.interval, last_run_at=last_run_at, now=now)
    if registered.crontab is not None:
        return is_crontab_due(
            crontab=registered.crontab,
            last_run_at=last_run_at,
            now=now,
            tick_window=tick_window,
        )
    return False


def utc_now() -> datetime:
    return datetime.now(UTC)

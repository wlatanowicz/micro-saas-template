from __future__ import annotations

from datetime import UTC, datetime, timedelta

from cron_converter import Cron

from src.scheduler.due_checks import is_crontab_due, is_interval_due, is_task_due
from src.scheduler.registry import RegisteredTask


def test_interval_due_when_never_run() -> None:
    now = datetime(2026, 6, 15, 12, 0, tzinfo=UTC)
    assert is_interval_due(interval=timedelta(hours=1), last_run_at=None, now=now)


def test_interval_not_due_before_next_run() -> None:
    now = datetime(2026, 6, 15, 12, 0, tzinfo=UTC)
    last_run = datetime(2026, 6, 15, 11, 30, tzinfo=UTC)
    assert not is_interval_due(interval=timedelta(hours=1), last_run_at=last_run, now=now)


def test_interval_due_after_elapsed() -> None:
    now = datetime(2026, 6, 15, 12, 0, tzinfo=UTC)
    last_run = datetime(2026, 6, 15, 10, 0, tzinfo=UTC)
    assert is_interval_due(interval=timedelta(hours=1), last_run_at=last_run, now=now)


def test_crontab_due_on_hourly_slot() -> None:
    now = datetime(2026, 6, 15, 12, 0, tzinfo=UTC)
    crontab = Cron("0 * * * *")
    assert is_crontab_due(
        crontab=crontab,
        last_run_at=datetime(2026, 6, 15, 11, 0, tzinfo=UTC),
        now=now,
        tick_window=timedelta(hours=1),
    )


def test_crontab_not_due_before_next_slot() -> None:
    now = datetime(2026, 6, 15, 12, 30, tzinfo=UTC)
    crontab = Cron("0 * * * *")
    assert not is_crontab_due(
        crontab=crontab,
        last_run_at=datetime(2026, 6, 15, 12, 0, tzinfo=UTC),
        now=now,
        tick_window=timedelta(hours=1),
    )


def test_is_task_due_uses_interval() -> None:
    now = datetime(2026, 6, 15, 12, 0, tzinfo=UTC)
    registered = RegisteredTask(
        function_path="example.task",
        function=lambda: None,
        queue="MESSAGES",
        interval=timedelta(minutes=5),
    )
    assert is_task_due(
        registered,
        last_run_at=datetime(2026, 6, 15, 11, 0, tzinfo=UTC),
        now=now,
        tick_window=timedelta(hours=1),
    )

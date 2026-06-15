from __future__ import annotations

from contextlib import contextmanager
from datetime import UTC, datetime

import pytest

from src.scheduler.due import run_due_tasks
from src.scheduler.models import SchedulerTaskRun
from src.scheduler.tests import sample_tasks


@pytest.fixture(autouse=True)
def _clear_executions(monkeypatch: pytest.MonkeyPatch) -> None:
    sample_tasks.INTERVAL_EXECUTIONS.clear()
    sample_tasks.CRONTAB_EXECUTIONS.clear()
    monkeypatch.setattr("src.scheduler.config.SCHEDULER_TRANSPORT", "sync")


def test_run_due_tasks_enqueues_interval_task_and_records_last_run() -> None:
    now = datetime(2026, 6, 15, 12, 0, tzinfo=UTC)
    records: dict[str, SchedulerTaskRun] = {}

    class FakeSession:
        def get(self, model: type[SchedulerTaskRun], key: str) -> SchedulerTaskRun | None:
            return records.get(key)

        def add(self, obj: SchedulerTaskRun) -> None:
            records[obj.function_path] = obj

    @contextmanager
    def fake_session_scope():
        yield FakeSession()

    with pytest.MonkeyPatch.context() as mp:
        mp.setattr("src.scheduler.due.session_scope", fake_session_scope)
        enqueued = run_due_tasks(now=now)

    interval_path = (
        f"{sample_tasks.interval_sample_task.__module__}."
        f"{sample_tasks.interval_sample_task.__qualname__}"
    )
    crontab_path = (
        f"{sample_tasks.crontab_sample_task.__module__}."
        f"{sample_tasks.crontab_sample_task.__qualname__}"
    )

    assert interval_path in enqueued
    assert crontab_path in enqueued
    assert sample_tasks.INTERVAL_EXECUTIONS == ["default"]
    assert sample_tasks.CRONTAB_EXECUTIONS == ["default"]
    assert records[interval_path].last_run_at == now
    assert records[crontab_path].last_run_at == now


def test_run_due_tasks_skips_task_not_yet_due() -> None:
    now = datetime(2026, 6, 15, 12, 0, tzinfo=UTC)
    interval_path = (
        f"{sample_tasks.interval_sample_task.__module__}."
        f"{sample_tasks.interval_sample_task.__qualname__}"
    )
    records = {
        interval_path: SchedulerTaskRun(
            function_path=interval_path,
            last_run_at=datetime(2026, 6, 15, 11, 59, tzinfo=UTC),
        ),
    }

    class FakeSession:
        def get(self, model: type[SchedulerTaskRun], key: str) -> SchedulerTaskRun | None:
            return records.get(key)

        def add(self, obj: SchedulerTaskRun) -> None:
            records[obj.function_path] = obj

    @contextmanager
    def fake_session_scope():
        yield FakeSession()

    with pytest.MonkeyPatch.context() as mp:
        mp.setattr("src.scheduler.due.session_scope", fake_session_scope)
        enqueued = run_due_tasks(now=now)

    assert interval_path not in enqueued
    assert sample_tasks.INTERVAL_EXECUTIONS == []

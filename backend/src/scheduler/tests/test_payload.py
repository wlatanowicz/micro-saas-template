from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest

from src.scheduler.payload import TaskPayload
from src.scheduler.registry import RegisteredTask


def _registered(*, expire: timedelta | None = None) -> RegisteredTask:
    return RegisteredTask(
        function_path="app.tasks.do_work",
        function=lambda: None,
        queue="MESSAGES",
        expire=expire,
    )


def test_for_task_includes_created_at_and_expire_seconds() -> None:
    created_at = datetime(2026, 6, 15, 12, 0, tzinfo=UTC)
    payload = TaskPayload.for_task(
        _registered(expire=timedelta(minutes=5)),
        "hello",
        flag=True,
        created_at=created_at,
    )
    assert payload.function_path == "app.tasks.do_work"
    assert payload.args == ["hello"]
    assert payload.kwargs == {"flag": True}
    assert payload.created_at == created_at
    assert payload.expire_seconds == 300.0
    assert payload.retry == 0


def test_for_task_omits_expire_seconds_when_not_set() -> None:
    payload = TaskPayload.for_task(_registered(), "hello")
    assert payload.expire_seconds is None


def test_to_dict_serializes_payload() -> None:
    created_at = datetime(2026, 6, 15, 12, 0, tzinfo=UTC)
    payload = TaskPayload.for_task(
        _registered(expire=timedelta(minutes=5)),
        "hello",
        created_at=created_at,
    )
    data = payload.to_dict()
    assert data["function_path"] == "app.tasks.do_work"
    assert data["args"] == ["hello"]
    assert data["kwargs"] == {}
    assert data["created_at"] == "2026-06-15T12:00:00+00:00"
    assert data["expire_seconds"] == 300.0
    assert data["retry"] == 0


def test_from_dict_round_trip() -> None:
    created_at = datetime(2026, 6, 15, 12, 0, tzinfo=UTC)
    original = TaskPayload.for_task(
        _registered(expire=timedelta(minutes=5)),
        "hello",
        flag=True,
        created_at=created_at,
    )
    restored = TaskPayload.from_dict(original.to_dict())
    assert restored == original


def test_from_dict_requires_created_at() -> None:
    with pytest.raises(KeyError, match="created_at"):
        TaskPayload.from_dict(
            {
                "function_path": "app.tasks.do_work",
                "args": ["hello"],
                "kwargs": {},
            }
        )


def test_is_expired_when_past_deadline() -> None:
    created_at = datetime(2026, 6, 15, 12, 0, tzinfo=UTC)
    payload = TaskPayload(
        function_path="app.tasks.do_work",
        args=[],
        kwargs={},
        created_at=created_at,
        expire_seconds=300.0,
    )
    now = created_at + timedelta(minutes=5)
    assert payload.is_expired(now=now)
    assert not payload.is_expired(now=now - timedelta(seconds=1))


def test_is_expired_without_expire_seconds() -> None:
    created_at = datetime(2026, 6, 15, 12, 0, tzinfo=UTC)
    payload = TaskPayload(
        function_path="app.tasks.do_work",
        args=[],
        kwargs={},
        created_at=created_at,
    )
    assert not payload.is_expired(now=created_at + timedelta(days=1))


def test_from_dict_rejects_invalid_args_type() -> None:
    with pytest.raises(TypeError, match="payload args must be a list"):
        TaskPayload.from_dict({"function_path": "app.tasks.do_work", "args": "bad"})


def test_from_dict_defaults_retry_to_zero() -> None:
    created_at = datetime(2026, 6, 15, 12, 0, tzinfo=UTC)
    payload = TaskPayload.from_dict(
        {
            "function_path": "app.tasks.do_work",
            "args": [],
            "kwargs": {},
            "created_at": created_at.isoformat(),
        }
    )
    assert payload.retry == 0


def test_from_dict_rejects_invalid_retry_type() -> None:
    with pytest.raises(TypeError, match="payload retry must be an int"):
        TaskPayload.from_dict(
            {
                "function_path": "app.tasks.do_work",
                "args": [],
                "kwargs": {},
                "created_at": datetime(2026, 6, 15, 12, 0, tzinfo=UTC).isoformat(),
                "retry": "bad",
            }
        )


def test_with_retry_returns_updated_payload() -> None:
    created_at = datetime(2026, 6, 15, 12, 0, tzinfo=UTC)
    original = TaskPayload(
        function_path="app.tasks.do_work",
        args=["hello"],
        kwargs={"flag": True},
        created_at=created_at,
        expire_seconds=300.0,
        retry=1,
    )
    updated = original.with_retry(2)
    assert updated.retry == 2
    assert updated.function_path == original.function_path
    assert updated.args == original.args
    assert updated.kwargs == original.kwargs
    assert updated.created_at == original.created_at
    assert updated.expire_seconds == original.expire_seconds

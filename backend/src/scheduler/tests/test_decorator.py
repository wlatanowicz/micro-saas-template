from __future__ import annotations

from datetime import timedelta

import pytest
from cron_converter import Cron

from src import scheduler
from src.scheduler.registry import TASK_REGISTRY


def test_task_registers_in_global_registry() -> None:
    TASK_REGISTRY.clear()

    @scheduler.task(queue="MESSAGES")
    def send_message(sender: str, recipient: str, body: str) -> None:
        del sender, recipient, body

    path = f"{send_message.__module__}.{send_message.__qualname__}"
    assert path in TASK_REGISTRY
    registered = TASK_REGISTRY[path]
    assert registered.queue == "MESSAGES"
    assert registered.function_path == path
    assert registered.crontab is None
    assert registered.interval is None
    assert registered.expire is None
    assert registered.max_retries == 0
    assert callable(send_message)
    assert callable(send_message.enqueue)


def test_wrapped_function_has_enqueue() -> None:
    TASK_REGISTRY.clear()

    @scheduler.task(queue="MESSAGES")
    def send_message(sender: str, recipient: str, body: str) -> None:
        del sender, recipient, body

    assert callable(send_message.enqueue)


def test_crontab_string_is_parsed_to_cron() -> None:
    TASK_REGISTRY.clear()

    @scheduler.task(queue="MESSAGES", crontab="0 * * * *")
    def heartbeat(*, enabled: bool = True) -> None:
        del enabled

    path = f"{heartbeat.__module__}.{heartbeat.__qualname__}"
    registered = TASK_REGISTRY[path]
    assert isinstance(registered.crontab, Cron)
    assert registered.crontab.to_string() == "0 * * * *"


def test_rejects_crontab_and_interval_together() -> None:
    TASK_REGISTRY.clear()

    with pytest.raises(ValueError, match="only one of crontab or interval"):
        scheduler.task(
            queue="MESSAGES",
            crontab="0 * * * *",
            interval=timedelta(hours=1),
        )(lambda: None)


def test_rejects_required_parameters_for_scheduled_task() -> None:
    TASK_REGISTRY.clear()

    with pytest.raises(ValueError, match="required parameter 'value'"):
        scheduler.task(queue="MESSAGES", interval=timedelta(minutes=5))(
            lambda value: None,
        )


def test_accepts_scheduled_task_with_only_default_parameters() -> None:
    TASK_REGISTRY.clear()

    @scheduler.task(queue="MESSAGES", interval=timedelta(minutes=5))
    def cleanup(*, dry_run: bool = False) -> None:
        del dry_run

    path = f"{cleanup.__module__}.{cleanup.__qualname__}"
    assert path in TASK_REGISTRY


def test_task_registers_expire() -> None:
    TASK_REGISTRY.clear()

    @scheduler.task(queue="MESSAGES", expire=timedelta(minutes=10))
    def send_message(sender: str) -> None:
        del sender

    path = f"{send_message.__module__}.{send_message.__qualname__}"
    registered = TASK_REGISTRY[path]
    assert registered.expire == timedelta(minutes=10)


def test_task_registers_max_retries() -> None:
    TASK_REGISTRY.clear()

    @scheduler.task(queue="MESSAGES", max_retries=3)
    def send_message(sender: str) -> None:
        del sender

    path = f"{send_message.__module__}.{send_message.__qualname__}"
    registered = TASK_REGISTRY[path]
    assert registered.max_retries == 3

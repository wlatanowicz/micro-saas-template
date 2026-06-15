from __future__ import annotations

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
    assert callable(send_message)
    assert callable(send_message.enqueue)


def test_wrapped_function_has_enqueue() -> None:
    TASK_REGISTRY.clear()

    @scheduler.task(queue="MESSAGES")
    def send_message(sender: str, recipient: str, body: str) -> None:
        del sender, recipient, body

    assert callable(send_message.enqueue)

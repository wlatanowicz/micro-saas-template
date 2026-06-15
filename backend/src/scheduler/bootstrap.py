from __future__ import annotations


def bootstrap_task_registry() -> None:
    import src.apps.notifications.tasks  # noqa: F401

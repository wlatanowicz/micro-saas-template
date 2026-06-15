from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

TASK_REGISTRY: dict[str, RegisteredTask] = {}


@dataclass(frozen=True, slots=True)
class RegisteredTask:
    function_path: str
    function: Callable[..., Any]
    queue: str

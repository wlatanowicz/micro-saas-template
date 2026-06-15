from __future__ import annotations

import importlib
from typing import Any


def _resolve_attr(module: object, qualname: str) -> Any:
    obj: object = module
    for part in qualname.split("."):
        obj = getattr(obj, part)
    return obj


def execute_task(function_path: str, args: list[Any], kwargs: dict[str, Any]) -> Any:
    module_path, _, qualname = function_path.rpartition(".")
    if not module_path or not qualname:
        msg = f"invalid function_path: {function_path!r}"
        raise ValueError(msg)
    module = importlib.import_module(module_path)
    func = _resolve_attr(module, qualname)
    if not callable(func):
        msg = f"{function_path!r} is not callable"
        raise TypeError(msg)
    return func(*args, **kwargs)

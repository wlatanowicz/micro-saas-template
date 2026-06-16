from __future__ import annotations

import importlib
import importlib.util
import pkgutil
from pathlib import Path

_APPS_PACKAGE = "src.apps"


def bootstrap_task_registry() -> None:
    apps_path = Path(__file__).resolve().parent.parent / "apps"
    prefix = f"{_APPS_PACKAGE}."
    for module_info in pkgutil.iter_modules([str(apps_path)], prefix):
        if not module_info.ispkg:
            continue
        tasks_module = f"{module_info.name}.tasks"
        if importlib.util.find_spec(tasks_module) is None:
            continue
        importlib.import_module(tasks_module)

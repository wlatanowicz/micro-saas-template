from __future__ import annotations

import importlib
from unittest.mock import patch

from src.scheduler.bootstrap import bootstrap_task_registry


def test_bootstrap_task_registry_imports_all_app_tasks_modules() -> None:
    with patch.object(importlib, "import_module", wraps=importlib.import_module) as mock_import:
        bootstrap_task_registry()

    imported = [call.args[0] for call in mock_import.call_args_list]
    assert imported == ["src.apps.notifications.tasks"]

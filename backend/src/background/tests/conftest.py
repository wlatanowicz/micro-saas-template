from __future__ import annotations

import importlib

import pytest

from src.background.tests import sample_tasks


@pytest.fixture(autouse=True)
def _register_sample_tasks() -> None:
    importlib.reload(sample_tasks)

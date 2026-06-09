from __future__ import annotations

import pytest
from fastapi.testclient import TestClient
from src.main import app


def _no_database_url() -> str | None:
    return None


def _patch_no_database(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("src.utils.db.get_database_url", _no_database_url)
    monkeypatch.setattr("src.utils.deps.get_database_url", _no_database_url)
    monkeypatch.setattr("src.apps.health.routes.get_database_url", _no_database_url)


@pytest.fixture
def client(monkeypatch: pytest.MonkeyPatch) -> TestClient:
    _patch_no_database(monkeypatch)
    return TestClient(app)

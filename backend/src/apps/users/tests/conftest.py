from __future__ import annotations

import os
from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text
from tests.db_schema import prepare_postgres_for_integration_tests

from src.main import app
from src.utils.db import get_engine


@pytest.fixture(scope="session")
def postgres_integration() -> Iterator[None]:
    """Real Postgres: clear schema + Alembic migrations, then pool reset (see skill / README)."""
    url = os.environ.get("DATABASE_URL", "").strip()
    if not url:
        pytest.skip(
            "DATABASE_URL not set — use `make test-be` (ephemeral Postgres) or export "
            "DATABASE_URL for integration tests",
        )
    os.environ.setdefault(
        "JWT_SECRET",
        "test-jwt-secret-key-at-least-thirty-two-chars-for-local-and-ci",
    )
    prepare_postgres_for_integration_tests()
    yield


def _truncate_app_tables() -> None:
    engine = get_engine()
    with engine.begin() as conn:
        conn.execute(
            text(
                "TRUNCATE TABLE user_identities, verification_codes, users, items "
                "RESTART IDENTITY CASCADE"
            ),
        )


@pytest.fixture
def auth_client(postgres_integration) -> TestClient:
    _truncate_app_tables()
    return TestClient(app)

"""Reset Postgres and apply migrations before integration tests.

Matches the **Reset and initialize the test database** flow in the api-testing skill:
clear schema, then ``alembic upgrade head`` (same path as production).
"""

from __future__ import annotations

import os
from contextlib import contextmanager
from pathlib import Path
from urllib.parse import urlparse

from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, text
from src.utils.db import reinit_engine

BACKEND_ROOT = Path(__file__).resolve().parent.parent


def _is_postgres_url(url: str) -> bool:
    try:
        scheme = urlparse(url).scheme
    except ValueError:
        return False
    return scheme.startswith("postgresql")


@contextmanager
def _working_directory(path: Path):
    prev = os.getcwd()
    os.chdir(path)
    try:
        yield
    finally:
        os.chdir(prev)


def prepare_postgres_for_integration_tests() -> None:
    """Clear ``public`` schema and migrate to head. Destructive — use a disposable DATABASE_URL."""
    url = os.environ.get("DATABASE_URL", "").strip()
    if not url:
        msg = "DATABASE_URL must be set"
        raise RuntimeError(msg)
    if not _is_postgres_url(url):
        prefix = url.split(":", 1)[0]
        msg = f"Integration tests expect a PostgreSQL DATABASE_URL, got {prefix}"
        raise RuntimeError(msg)

    # Drop pooled connections before tearing down schema.
    reinit_engine()

    admin = create_engine(url, isolation_level="AUTOCOMMIT")
    with admin.connect() as conn:
        conn.execute(text("DROP SCHEMA IF EXISTS public CASCADE"))
        conn.execute(text("CREATE SCHEMA public"))
        conn.execute(text("GRANT ALL ON SCHEMA public TO CURRENT_USER"))
        conn.execute(text("GRANT ALL ON SCHEMA public TO PUBLIC"))
    admin.dispose()

    cfg = Config(str(BACKEND_ROOT / "alembic.ini"))
    with _working_directory(BACKEND_ROOT):
        command.upgrade(cfg, "head")

    reinit_engine()

"""Database engine and sessions. Uses short-lived connections suitable for Lambda.

For production workloads against RDS, use RDS Proxy and tune pool settings.
"""

from __future__ import annotations

import enum
import os
from collections.abc import Generator
from contextlib import contextmanager
from typing import Any

from sqlalchemy import Enum, create_engine
from sqlalchemy.orm import sessionmaker
from sqlmodel import Session, SQLModel

_engine = None
_SessionLocal = None


def to_sql_enum(enums: type[enum.Enum], **kw: Any) -> Enum:
    def get_enum_values(enum_class: type[enum.Enum]) -> list[Any]:
        return [member.value for member in enum_class]

    return Enum(enums, values_callable=get_enum_values, **kw)


def get_database_url() -> str | None:
    url = os.environ.get("DATABASE_URL", "").strip()
    return url or None


def init_engine():
    global _engine, _SessionLocal
    url = get_database_url()
    if not url:
        return
    # Lambda: small pool, dispose between invocations is handled by container freeze
    _engine = create_engine(
        url,
        pool_pre_ping=True,
        pool_size=1,
        max_overflow=0,
    )
    _SessionLocal = sessionmaker(
        bind=_engine,
        class_=Session,
        expire_on_commit=False,
    )


init_engine()


@contextmanager
def session_scope() -> Generator[Session, None, None]:
    if _SessionLocal is None:
        raise RuntimeError("DATABASE_URL is not set")
    session = _SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def create_db_and_tables() -> None:
    """Create tables (local/dev helper). Migrations should use Alembic in deployed environments."""
    if _engine is None:
        return
    SQLModel.metadata.create_all(_engine)

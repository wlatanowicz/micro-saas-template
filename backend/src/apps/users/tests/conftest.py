from __future__ import annotations

from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.engine import Engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from sqlmodel import Session, SQLModel, create_engine

from src.main import app
from src.utils.deps import get_db_session


@pytest.fixture
def sqlite_auth_engine(monkeypatch: pytest.MonkeyPatch) -> Engine:
    monkeypatch.setenv("JWT_SECRET", "test-jwt-secret-key-at-least-thirty-two-chars")
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)
    return engine


@pytest.fixture
def auth_client(sqlite_auth_engine: Engine) -> Generator[TestClient, None, None]:
    SessionLocal = sessionmaker(bind=sqlite_auth_engine, class_=Session, expire_on_commit=False)

    def override_get_db_session() -> Generator[Session, None, None]:
        session = SessionLocal()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    app.dependency_overrides[get_db_session] = override_get_db_session
    yield TestClient(app)
    app.dependency_overrides.pop(get_db_session, None)

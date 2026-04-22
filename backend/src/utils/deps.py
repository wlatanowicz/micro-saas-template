from __future__ import annotations

from src.utils.db import get_database_url, session_scope


def get_db_session():
    if not get_database_url():
        yield None
        return
    with session_scope() as session:
        yield session

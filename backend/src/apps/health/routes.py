from __future__ import annotations

from fastapi import APIRouter

from src.utils.db import get_database_url

router = APIRouter(tags=["health"])


@router.get("/health")
def health():
    return {"status": "ok", "database_configured": bool(get_database_url())}

from __future__ import annotations

import os

from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlmodel import Session, select

from src.db import get_database_url, session_scope
from src.models import Item

app = FastAPI(title="Micro-SaaS API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=os.environ.get("CORS_ALLOW_ORIGINS", "*").split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def get_db_session():
    if not get_database_url():
        yield None
        return
    with session_scope() as session:
        yield session


class ItemCreate(BaseModel):
    name: str


@app.get("/health")
def health():
    return {"status": "ok", "database_configured": bool(get_database_url())}


@app.get("/api/items")
def list_items(session: Session | None = Depends(get_db_session)):
    if session is None:
        return {"items": [], "detail": "database not configured"}
    items = list(session.exec(select(Item)).all())
    return {"items": [{"id": i.id, "name": i.name} for i in items]}


@app.post("/api/items")
def create_item(
    payload: ItemCreate,
    session: Session | None = Depends(get_db_session),
):
    if session is None:
        raise HTTPException(status_code=503, detail="database not configured")
    item = Item(name=payload.name.strip())
    session.add(item)
    session.flush()
    session.refresh(item)
    return {"id": item.id, "name": item.name}

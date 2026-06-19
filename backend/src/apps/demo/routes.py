from __future__ import annotations

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlmodel import Session, select

from src.apps.demo.api_errors import ApiErrorCode
from src.apps.demo.models import Item
from src.utils.api_errors import raise_api_error
from src.utils.deps import get_db_session

router = APIRouter(prefix="/api/items", tags=["items"])


class ItemCreate(BaseModel):
    name: str


@router.get("")
def list_items(session: Session | None = Depends(get_db_session)):
    if session is None:
        return {
            "items": [],
            "detail": "database not configured",
            "detail_code": ApiErrorCode.database_not_configured,
        }
    items = list(session.exec(select(Item)).all())
    return {"items": [{"id": i.id, "name": i.name} for i in items]}


@router.post("")
def create_item(
    payload: ItemCreate,
    session: Session | None = Depends(get_db_session),
):
    if session is None:
        raise_api_error(
            ApiErrorCode.database_not_configured,
            "database not configured",
            status_code=503,
        )
    item = Item(name=payload.name.strip())
    session.add(item)
    session.flush()
    session.refresh(item)
    return {"id": item.id, "name": item.name}

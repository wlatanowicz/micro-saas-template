from __future__ import annotations

from enum import StrEnum
from typing import Any

from fastapi import HTTPException
from pydantic import BaseModel


class CommonApiErrorCode(StrEnum):
    request_validation_error = "request_validation_error"


class ApiErrorDetail(BaseModel):
    code: str
    message: str
    params: dict[str, Any] | None = None


def raise_api_error(
    code: StrEnum | str,
    message: str,
    status_code: int,
    params: dict[str, Any] | None = None,
) -> None:
    detail = ApiErrorDetail(
        code=str(code),
        message=message,
        params=params,
    )
    raise HTTPException(status_code=status_code, detail=detail.model_dump())


def api_error_code_from_detail(detail: object) -> str | None:
    if isinstance(detail, dict) and "code" in detail:
        return str(detail["code"])
    return None

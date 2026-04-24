from __future__ import annotations

import enum
from uuid import UUID, uuid4

from sqlmodel import Column, Field, SQLModel

from src.utils.db import to_sql_enum


class UserStatus(enum.StrEnum):
    active = "active"
    inactive = "inactive"
    disabled = "disabled"


class User(SQLModel, table=True):
    __tablename__ = "users"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    email: str = Field(max_length=255, index=True, unique=True)
    hashed_password: str = Field(max_length=255)
    status: UserStatus = Field(
        default=UserStatus.active,
        sa_column=Column(to_sql_enum(UserStatus, name="userstatus"), nullable=False),
    )

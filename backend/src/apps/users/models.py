from __future__ import annotations

import enum
from uuid import UUID, uuid4

from sqlalchemy import Enum as SAEnum
from sqlmodel import Column, Field, SQLModel


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
        sa_column=Column(
            SAEnum(
                UserStatus,
                name="userstatus",
                create_constraint=True,
                native_enum=False,
                values_callable=lambda x: [e.value for e in x],
            ),
            nullable=False,
        ),
    )

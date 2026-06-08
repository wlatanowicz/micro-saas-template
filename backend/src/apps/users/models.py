from __future__ import annotations

import enum
from uuid import UUID, uuid4

from sqlalchemy import UniqueConstraint
from sqlmodel import Column, Field, SQLModel

from src.utils.db import to_sql_enum


class UserStatus(enum.StrEnum):
    active = "active"
    inactive = "inactive"
    disabled = "disabled"


class AuthProvider(enum.StrEnum):
    google = "google"
    facebook = "facebook"


class User(SQLModel, table=True):
    __tablename__ = "users"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    email: str = Field(max_length=255, index=True, unique=True)
    hashed_password: str | None = Field(default=None, max_length=255)
    status: UserStatus = Field(
        default=UserStatus.active,
        sa_column=Column(to_sql_enum(UserStatus, name="userstatus"), nullable=False),
    )


class UserIdentity(SQLModel, table=True):
    __tablename__ = "user_identities"
    __table_args__ = (UniqueConstraint("provider", "provider_subject"),)

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    user_id: UUID = Field(foreign_key="users.id", index=True)
    provider: AuthProvider = Field(
        sa_column=Column(to_sql_enum(AuthProvider, name="authprovider"), nullable=False),
    )
    provider_subject: str = Field(max_length=255)

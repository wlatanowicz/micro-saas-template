from __future__ import annotations

import os
from datetime import UTC, datetime, timedelta
from uuid import UUID

import jwt
from fastapi import HTTPException
from passlib.context import CryptContext

from src.utils.db import get_database_url

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

JWT_ALGORITHM = "HS256"
MIN_PASSWORD_LENGTH = 8
DEFAULT_JWT_EXPIRE_MINUTES = 60 * 24 * 7  # 7 days


def get_jwt_secret() -> str | None:
    secret = os.environ.get("JWT_SECRET", "").strip()
    return secret or None


def hash_password(plain: str) -> str:
    return pwd_context.hash(plain)


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


def normalize_email(email: str) -> str:
    return email.strip().lower()


def create_access_token(user_id: UUID) -> str:
    secret = get_jwt_secret()
    if not secret:
        msg = "JWT_SECRET is not configured"
        raise RuntimeError(msg)
    minutes = int(os.environ.get("JWT_EXPIRE_MINUTES", str(DEFAULT_JWT_EXPIRE_MINUTES)))
    expire = datetime.now(UTC) + timedelta(minutes=minutes)
    return jwt.encode(
        {"sub": str(user_id), "exp": expire},
        secret,
        algorithm=JWT_ALGORITHM,
    )


def decode_token(token: str) -> dict:
    secret = get_jwt_secret()
    if not secret:
        msg = "JWT_SECRET is not configured"
        raise RuntimeError(msg)
    return jwt.decode(token, secret, algorithms=[JWT_ALGORITHM])


def ensure_auth_configured() -> None:
    """If the API has a database, signing tokens requires JWT_SECRET."""
    if not get_database_url() or get_jwt_secret():
        return
    raise HTTPException(
        status_code=503,
        detail="auth not configured (set JWT_SECRET)",
    )

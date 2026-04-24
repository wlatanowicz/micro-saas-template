from __future__ import annotations

import hashlib
import os
from datetime import UTC, datetime, timedelta
from uuid import UUID

import bcrypt
import jwt
from fastapi import HTTPException

from src.utils.db import get_database_url

JWT_ALGORITHM = "HS256"
MIN_PASSWORD_LENGTH = 8
DEFAULT_JWT_EXPIRE_MINUTES = 60 * 24 * 7  # 7 days


def get_jwt_secret() -> str | None:
    secret = os.environ.get("JWT_SECRET", "").strip()
    return secret or None


def _password_digest(plain: str) -> bytes:
    """32-byte digest so bcrypt never sees secrets longer than its 72-byte limit."""
    return hashlib.sha256(plain.encode("utf-8")).digest()


def hash_password(plain: str) -> str:
    return bcrypt.hashpw(_password_digest(plain), bcrypt.gensalt()).decode("ascii")


def verify_password(plain: str, hashed: str) -> bool:
    h = hashed.encode("ascii")
    if bcrypt.checkpw(_password_digest(plain), h):
        return True
    # Accounts created before pre-hashing: bcrypt(raw utf-8), only valid if <= 72 bytes.
    legacy = plain.encode("utf-8")
    if len(legacy) > 72:
        return False
    return bcrypt.checkpw(legacy, h)


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

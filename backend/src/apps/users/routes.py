from __future__ import annotations

from uuid import UUID

import jwt
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel, field_validator
from sqlmodel import Session, select

from src.apps.users.auth import (
    MIN_PASSWORD_LENGTH,
    create_access_token,
    decode_token,
    ensure_auth_configured,
    hash_password,
    normalize_email,
    verify_password,
)
from src.apps.users.models import User, UserStatus
from src.utils.deps import get_db_session

router = APIRouter(prefix="/api/auth", tags=["auth"])
bearer = HTTPBearer(auto_error=False)


def _email_field(v: str) -> str:
    s = normalize_email(v)
    if "@" not in s or s.index("@") < 1:
        msg = "invalid email"
        raise ValueError(msg)
    return s


class SignUpIn(BaseModel):
    email: str
    password: str

    @field_validator("email")
    @classmethod
    def email_normalized(cls, v: str) -> str:
        return _email_field(v)

    @field_validator("password")
    @classmethod
    def password_strength(cls, v: str) -> str:
        if len(v) < MIN_PASSWORD_LENGTH:
            msg = f"password must be at least {MIN_PASSWORD_LENGTH} characters"
            raise ValueError(msg)
        return v


class SignInIn(BaseModel):
    email: str
    password: str

    @field_validator("email")
    @classmethod
    def email_normalized(cls, v: str) -> str:
        return _email_field(v)


class UserPublic(BaseModel):
    id: UUID
    email: str
    status: str


class TokenOut(BaseModel):
    access_token: str
    token_type: str
    user: UserPublic


@router.post("/signup", response_model=TokenOut, status_code=status.HTTP_201_CREATED)
def signup(
    body: SignUpIn,
    session: Session | None = Depends(get_db_session),
) -> dict:
    if session is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="database not configured",
        )
    ensure_auth_configured()
    existing = session.exec(select(User).where(User.email == body.email)).first()
    if existing is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="email already registered",
        )
    user = User(
        email=body.email,
        hashed_password=hash_password(body.password),
        status=UserStatus.active,
    )
    session.add(user)
    session.flush()
    session.refresh(user)
    token = create_access_token(user.id)
    return {
        "access_token": token,
        "token_type": "bearer",
        "user": UserPublic(
            id=user.id,
            email=user.email,
            status=user.status.value,
        ),
    }


@router.post("/signin", response_model=TokenOut)
def signin(
    body: SignInIn,
    session: Session | None = Depends(get_db_session),
) -> dict:
    if session is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="database not configured",
        )
    ensure_auth_configured()
    user = session.exec(select(User).where(User.email == body.email)).first()
    if user is None or not verify_password(body.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )
    if user.status != UserStatus.active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is not active",
        )
    token = create_access_token(user.id)
    return {
        "access_token": token,
        "token_type": "bearer",
        "user": UserPublic(
            id=user.id,
            email=user.email,
            status=user.status.value,
        ),
    }


@router.get("/me", response_model=UserPublic)
def me(
    creds: HTTPAuthorizationCredentials | None = Depends(bearer),
    session: Session | None = Depends(get_db_session),
) -> UserPublic:
    if session is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="database not configured",
        )
    ensure_auth_configured()
    if creds is None or creds.scheme.lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
        )
    try:
        payload = decode_token(creds.credentials)
    except jwt.PyJWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        ) from None
    try:
        user_id = UUID(str(payload["sub"]))
    except (KeyError, TypeError, ValueError) as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
        ) from e
    user = session.get(User, user_id)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )
    if user.status != UserStatus.active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is not active",
        )
    return UserPublic(
        id=user.id,
        email=user.email,
        status=user.status.value,
    )

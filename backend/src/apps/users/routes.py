from __future__ import annotations

from uuid import UUID

import jwt
from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel, field_validator
from sqlmodel import Session, select

from src.apps.users import config
from src.apps.users.auth import (
    MIN_PASSWORD_LENGTH,
    create_access_token,
    decode_token,
    ensure_auth_configured,
    hash_password,
    normalize_email,
    verify_password,
)
from src.apps.users.guards import ensure_provider_configured, require_method_enabled
from src.apps.users.models import User, UserStatus
from src.apps.users.oauth import (
    authorize_redirect,
    complete_facebook_callback,
    complete_google_callback,
)
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


class AuthConfigOut(BaseModel):
    password: bool
    google: bool
    facebook: bool


@router.get("/config", response_model=AuthConfigOut)
def auth_config() -> AuthConfigOut:
    return AuthConfigOut(
        password=config.AUTH_PASSWORD_ENABLED,
        google=config.AUTH_GOOGLE_ENABLED,
        facebook=config.AUTH_FACEBOOK_ENABLED,
    )


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
    require_method_enabled("password")
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
    require_method_enabled("password")
    user = session.exec(select(User).where(User.email == body.email)).first()
    if (
        user is None
        or user.hashed_password is None
        or not verify_password(body.password, user.hashed_password)
    ):
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


@router.get("/google")
async def google_start(request: Request) -> object:
    require_method_enabled("google")
    ensure_auth_configured()
    ensure_provider_configured("google")
    return await authorize_redirect(request, "google", "google_callback")


@router.get("/google/callback", name="google_callback")
async def google_callback(
    request: Request,
    session: Session | None = Depends(get_db_session),
) -> object:
    if session is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="database not configured",
        )
    ensure_auth_configured()
    require_method_enabled("google")
    ensure_provider_configured("google")
    return await complete_google_callback(request, session)


@router.get("/facebook")
async def facebook_start(request: Request) -> object:
    require_method_enabled("facebook")
    ensure_auth_configured()
    ensure_provider_configured("facebook")
    return await authorize_redirect(request, "facebook", "facebook_callback")


@router.get("/facebook/callback", name="facebook_callback")
async def facebook_callback(
    request: Request,
    session: Session | None = Depends(get_db_session),
) -> object:
    if session is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="database not configured",
        )
    ensure_auth_configured()
    require_method_enabled("facebook")
    ensure_provider_configured("facebook")
    return await complete_facebook_callback(request, session)

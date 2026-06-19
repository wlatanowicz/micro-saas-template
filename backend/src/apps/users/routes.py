from __future__ import annotations

from uuid import UUID

import jwt
from fastapi import APIRouter, Depends, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel, field_validator
from sqlmodel import Session, select

from src.apps.users import config
from src.apps.users.api_errors import ApiErrorCode
from src.apps.users.auth import (
    MIN_PASSWORD_LENGTH,
    create_access_token,
    decode_token,
    ensure_auth_configured,
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
from src.apps.users.verification import (
    complete_password_recovery,
    complete_registration,
    send_password_recovery_code,
    send_registration_code,
    verify_password_recovery_code,
    verify_registration_code,
)
from src.utils.api_errors import raise_api_error
from src.utils.deps import get_db_session

router = APIRouter(prefix="/api/auth", tags=["auth"])
bearer = HTTPBearer(auto_error=False)

SEND_CODE_MESSAGE = "If an account is eligible, a verification code has been sent."


def _email_field(v: str) -> str:
    s = normalize_email(v)
    if "@" not in s or s.index("@") < 1:
        msg = "invalid email"
        raise ValueError(msg)
    return s


def _code_field(v: str) -> str:
    code = v.strip().upper()
    if len(code) != 6 or not code.isalnum() or not code.isascii():
        msg = "code must be 6 letters or digits"
        raise ValueError(msg)
    return code


class EmailIn(BaseModel):
    email: str

    @field_validator("email")
    @classmethod
    def email_normalized(cls, v: str) -> str:
        return _email_field(v)


class VerifyCodeIn(BaseModel):
    email: str
    code: str

    @field_validator("email")
    @classmethod
    def email_normalized(cls, v: str) -> str:
        return _email_field(v)

    @field_validator("code")
    @classmethod
    def code_normalized(cls, v: str) -> str:
        return _code_field(v)


class CompletePasswordIn(BaseModel):
    email: str
    code: str
    password: str
    password_confirm: str

    @field_validator("email")
    @classmethod
    def email_normalized(cls, v: str) -> str:
        return _email_field(v)

    @field_validator("code")
    @classmethod
    def code_normalized(cls, v: str) -> str:
        return _code_field(v)

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


class MessageOut(BaseModel):
    message: str


def _require_session(session: Session | None) -> Session:
    if session is None:
        raise_api_error(
            ApiErrorCode.database_not_configured,
            "database not configured",
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        )
    return session


@router.get("/config", response_model=AuthConfigOut)
def auth_config() -> AuthConfigOut:
    return AuthConfigOut(
        password=config.AUTH_PASSWORD_ENABLED,
        google=config.AUTH_GOOGLE_ENABLED,
        facebook=config.AUTH_FACEBOOK_ENABLED,
    )


@router.post("/register/send-code", response_model=MessageOut)
def register_send_code(
    body: EmailIn,
    session: Session | None = Depends(get_db_session),
) -> MessageOut:
    db = _require_session(session)
    ensure_auth_configured()
    require_method_enabled("password")
    send_registration_code(db, body.email)
    return MessageOut(message="Verification code sent")


@router.post("/register/verify-code", response_model=MessageOut)
def register_verify_code(
    body: VerifyCodeIn,
    session: Session | None = Depends(get_db_session),
) -> MessageOut:
    db = _require_session(session)
    ensure_auth_configured()
    require_method_enabled("password")
    verify_registration_code(db, body.email, body.code)
    return MessageOut(message="Verification code accepted")


@router.post("/register/complete", response_model=TokenOut, status_code=status.HTTP_201_CREATED)
def register_complete(
    body: CompletePasswordIn,
    session: Session | None = Depends(get_db_session),
) -> dict:
    db = _require_session(session)
    ensure_auth_configured()
    require_method_enabled("password")
    return complete_registration(
        db,
        email=body.email,
        code=body.code,
        password=body.password,
        password_confirm=body.password_confirm,
    )


@router.post("/password-recovery/send-code", response_model=MessageOut)
def password_recovery_send_code(
    body: EmailIn,
    session: Session | None = Depends(get_db_session),
) -> MessageOut:
    db = _require_session(session)
    ensure_auth_configured()
    require_method_enabled("password")
    send_password_recovery_code(db, body.email)
    return MessageOut(message=SEND_CODE_MESSAGE)


@router.post("/password-recovery/verify-code", response_model=MessageOut)
def password_recovery_verify_code(
    body: VerifyCodeIn,
    session: Session | None = Depends(get_db_session),
) -> MessageOut:
    db = _require_session(session)
    ensure_auth_configured()
    require_method_enabled("password")
    verify_password_recovery_code(db, body.email, body.code)
    return MessageOut(message="Verification code accepted")


@router.post("/password-recovery/complete", response_model=TokenOut)
def password_recovery_complete(
    body: CompletePasswordIn,
    session: Session | None = Depends(get_db_session),
) -> dict:
    db = _require_session(session)
    ensure_auth_configured()
    require_method_enabled("password")
    return complete_password_recovery(
        db,
        email=body.email,
        code=body.code,
        password=body.password,
        password_confirm=body.password_confirm,
    )


@router.post("/signin", response_model=TokenOut)
def signin(
    body: SignInIn,
    session: Session | None = Depends(get_db_session),
) -> dict:
    if session is None:
        raise_api_error(
            ApiErrorCode.database_not_configured,
            "database not configured",
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        )
    ensure_auth_configured()
    require_method_enabled("password")
    user = session.exec(select(User).where(User.email == body.email)).first()
    if (
        user is None
        or user.hashed_password is None
        or not verify_password(body.password, user.hashed_password)
    ):
        raise_api_error(
            ApiErrorCode.auth_invalid_credentials,
            "Invalid email or password",
            status_code=status.HTTP_401_UNAUTHORIZED,
        )
    if user.status != UserStatus.active:
        raise_api_error(
            ApiErrorCode.account_not_active,
            "Account is not active",
            status_code=status.HTTP_403_FORBIDDEN,
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
        raise_api_error(
            ApiErrorCode.database_not_configured,
            "database not configured",
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        )
    ensure_auth_configured()
    if creds is None or creds.scheme.lower() != "bearer":
        raise_api_error(
            ApiErrorCode.not_authenticated,
            "Not authenticated",
            status_code=status.HTTP_401_UNAUTHORIZED,
        )
    try:
        payload = decode_token(creds.credentials)
    except jwt.PyJWTError:
        raise_api_error(
            ApiErrorCode.invalid_or_expired_token,
            "Invalid or expired token",
            status_code=status.HTTP_401_UNAUTHORIZED,
        )
    try:
        user_id = UUID(str(payload["sub"]))
    except (KeyError, TypeError, ValueError):
        raise_api_error(
            ApiErrorCode.invalid_token,
            "Invalid token",
            status_code=status.HTTP_401_UNAUTHORIZED,
        )
    user = session.get(User, user_id)
    if user is None:
        raise_api_error(
            ApiErrorCode.user_not_found,
            "User not found",
            status_code=status.HTTP_401_UNAUTHORIZED,
        )
    if user.status != UserStatus.active:
        raise_api_error(
            ApiErrorCode.account_not_active,
            "Account is not active",
            status_code=status.HTTP_403_FORBIDDEN,
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
        raise_api_error(
            ApiErrorCode.database_not_configured,
            "database not configured",
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
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
        raise_api_error(
            ApiErrorCode.database_not_configured,
            "database not configured",
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        )
    ensure_auth_configured()
    require_method_enabled("facebook")
    ensure_provider_configured("facebook")
    return await complete_facebook_callback(request, session)

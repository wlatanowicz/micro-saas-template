from __future__ import annotations

import secrets
import string
from datetime import UTC, datetime, timedelta

from sqlmodel import Session, delete, select

from src.apps.notifications.service import send_templated_email
from src.apps.users.api_errors import ApiErrorCode
from src.apps.users.auth import (
    MIN_PASSWORD_LENGTH,
    create_access_token,
    hash_password,
    normalize_email,
)
from src.apps.users.models import User, UserStatus, VerificationCode, VerificationPurpose
from src.utils.api_errors import raise_api_error

CODE_ALPHABET = string.ascii_uppercase + string.digits
CODE_LENGTH = 6
CODE_VALID_MINUTES = 30

_TEMPLATE_BY_PURPOSE = {
    VerificationPurpose.registration: "registration_code",
    VerificationPurpose.password_recovery: "password_recovery_code",
}


def generate_code() -> str:
    return "".join(secrets.choice(CODE_ALPHABET) for _ in range(CODE_LENGTH))


def _now() -> datetime:
    return datetime.now(tz=UTC)


def _delete_pending_codes(
    session: Session,
    *,
    email: str,
    purpose: VerificationPurpose,
) -> None:
    session.exec(
        delete(VerificationCode).where(
            VerificationCode.email == email,
            VerificationCode.purpose == purpose,
            VerificationCode.consumed_at.is_(None),
        )
    )


def _get_active_code(
    session: Session,
    *,
    email: str,
    purpose: VerificationPurpose,
) -> VerificationCode | None:
    return session.exec(
        select(VerificationCode)
        .where(
            VerificationCode.email == email,
            VerificationCode.purpose == purpose,
            VerificationCode.consumed_at.is_(None),
        )
        .order_by(VerificationCode.created_at.desc())
    ).first()


def _validate_code_match(record: VerificationCode, code: str) -> None:
    if record.valid_until < _now():
        raise_api_error(
            ApiErrorCode.verification_code_expired,
            "Verification code has expired",
            status_code=400,
        )
    if not secrets.compare_digest(record.code, code.upper()):
        raise_api_error(
            ApiErrorCode.invalid_verification_code,
            "Invalid verification code",
            status_code=400,
        )


def _send_code_email(*, email: str, code: str, purpose: VerificationPurpose) -> None:
    template_base = _TEMPLATE_BY_PURPOSE[purpose]
    send_templated_email(
        template_base,
        to=email,
        context={
            "email": email,
            "code": code,
            "valid_minutes": str(CODE_VALID_MINUTES),
        },
        purpose=purpose.value,
    )


def send_registration_code(session: Session, email: str) -> None:
    existing = session.exec(select(User).where(User.email == email)).first()
    if existing is not None:
        raise_api_error(
            ApiErrorCode.email_already_registered,
            "email already registered",
            status_code=409,
        )
    code = generate_code()
    now = _now()
    _delete_pending_codes(session, email=email, purpose=VerificationPurpose.registration)
    session.add(
        VerificationCode(
            email=email,
            purpose=VerificationPurpose.registration,
            code=code,
            created_at=now,
            valid_until=now + timedelta(minutes=CODE_VALID_MINUTES),
        )
    )
    session.flush()
    _send_code_email(email=email, code=code, purpose=VerificationPurpose.registration)


def verify_registration_code(session: Session, email: str, code: str) -> None:
    record = _get_active_code(
        session,
        email=email,
        purpose=VerificationPurpose.registration,
    )
    if record is None:
        raise_api_error(
            ApiErrorCode.invalid_verification_code,
            "Invalid verification code",
            status_code=400,
        )
    _validate_code_match(record, code)
    record.verified_at = _now()
    session.add(record)
    session.flush()


def complete_registration(
    session: Session,
    *,
    email: str,
    code: str,
    password: str,
    password_confirm: str,
) -> dict:
    if password != password_confirm:
        raise_api_error(
            ApiErrorCode.passwords_do_not_match,
            "Passwords do not match",
            status_code=400,
        )
    if len(password) < MIN_PASSWORD_LENGTH:
        raise_api_error(
            ApiErrorCode.auth_password_too_short,
            f"password must be at least {MIN_PASSWORD_LENGTH} characters",
            status_code=422,
            params={"min_length": MIN_PASSWORD_LENGTH},
        )
    record = _get_active_code(
        session,
        email=email,
        purpose=VerificationPurpose.registration,
    )
    if record is None or record.verified_at is None:
        raise_api_error(
            ApiErrorCode.verification_code_not_verified,
            "Verification code has not been verified",
            status_code=400,
        )
    _validate_code_match(record, code)
    existing = session.exec(select(User).where(User.email == email)).first()
    if existing is not None:
        raise_api_error(
            ApiErrorCode.email_already_registered,
            "email already registered",
            status_code=409,
        )
    user = User(
        email=email,
        hashed_password=hash_password(password),
        status=UserStatus.active,
    )
    session.add(user)
    record.consumed_at = _now()
    session.add(record)
    session.flush()
    session.refresh(user)
    token = create_access_token(user.id)
    return {
        "access_token": token,
        "token_type": "bearer",
        "user": {
            "id": user.id,
            "email": user.email,
            "status": user.status.value,
        },
    }


def send_password_recovery_code(session: Session, email: str) -> None:
    user = session.exec(select(User).where(User.email == email)).first()
    if user is None:
        return
    code = generate_code()
    now = _now()
    _delete_pending_codes(
        session,
        email=email,
        purpose=VerificationPurpose.password_recovery,
    )
    session.add(
        VerificationCode(
            email=email,
            purpose=VerificationPurpose.password_recovery,
            code=code,
            created_at=now,
            valid_until=now + timedelta(minutes=CODE_VALID_MINUTES),
        )
    )
    session.flush()
    _send_code_email(email=email, code=code, purpose=VerificationPurpose.password_recovery)


def verify_password_recovery_code(session: Session, email: str, code: str) -> None:
    record = _get_active_code(
        session,
        email=email,
        purpose=VerificationPurpose.password_recovery,
    )
    if record is None:
        raise_api_error(
            ApiErrorCode.invalid_verification_code,
            "Invalid verification code",
            status_code=400,
        )
    _validate_code_match(record, code)
    record.verified_at = _now()
    session.add(record)
    session.flush()


def complete_password_recovery(
    session: Session,
    *,
    email: str,
    code: str,
    password: str,
    password_confirm: str,
) -> dict:
    if password != password_confirm:
        raise_api_error(
            ApiErrorCode.passwords_do_not_match,
            "Passwords do not match",
            status_code=400,
        )
    if len(password) < MIN_PASSWORD_LENGTH:
        raise_api_error(
            ApiErrorCode.auth_password_too_short,
            f"password must be at least {MIN_PASSWORD_LENGTH} characters",
            status_code=422,
            params={"min_length": MIN_PASSWORD_LENGTH},
        )
    user = session.exec(select(User).where(User.email == email)).first()
    if user is None:
        raise_api_error(
            ApiErrorCode.invalid_verification_code,
            "Invalid verification code",
            status_code=400,
        )
    record = _get_active_code(
        session,
        email=email,
        purpose=VerificationPurpose.password_recovery,
    )
    if record is None or record.verified_at is None:
        raise_api_error(
            ApiErrorCode.verification_code_not_verified,
            "Verification code has not been verified",
            status_code=400,
        )
    _validate_code_match(record, code)
    user.hashed_password = hash_password(password)
    record.consumed_at = _now()
    session.add(user)
    session.add(record)
    session.flush()
    session.refresh(user)
    token = create_access_token(user.id)
    return {
        "access_token": token,
        "token_type": "bearer",
        "user": {
            "id": user.id,
            "email": user.email,
            "status": user.status.value,
        },
    }


def normalize_verification_email(email: str) -> str:
    return normalize_email(email)

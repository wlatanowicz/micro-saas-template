from __future__ import annotations

from sqlmodel import select

from src.apps.users.models import VerificationCode, VerificationPurpose
from src.utils.db import session_scope


def _latest_code(email: str, purpose: VerificationPurpose) -> str:
    with session_scope() as session:
        record = session.exec(
            select(VerificationCode)
            .where(
                VerificationCode.email == email,
                VerificationCode.purpose == purpose,
            )
            .order_by(VerificationCode.created_at.desc())
        ).first()
        assert record is not None
        return record.code


def register_user(auth_client, email: str, password: str) -> dict:
    assert (
        auth_client.post("/api/auth/register/send-code", json={"email": email}).status_code
        == 200
    )
    code = _latest_code(email, VerificationPurpose.registration)
    assert (
        auth_client.post(
            "/api/auth/register/verify-code",
            json={"email": email, "code": code},
        ).status_code
        == 200
    )
    r = auth_client.post(
        "/api/auth/register/complete",
        json={
            "email": email,
            "code": code,
            "password": password,
            "password_confirm": password,
        },
    )
    assert r.status_code == 201
    return r.json()

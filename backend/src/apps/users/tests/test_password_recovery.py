from __future__ import annotations

from uuid import uuid4

from fastapi.testclient import TestClient
from sqlmodel import select

from src.apps.users.api_errors import ApiErrorCode
from src.apps.users.models import (
    AuthProvider,
    User,
    UserIdentity,
    UserStatus,
    VerificationPurpose,
)
from src.apps.users.tests.helpers import _latest_code, register_user
from src.utils.db import session_scope


def test_password_recovery_send_code_without_database(client: TestClient) -> None:
    r = client.post("/api/auth/password-recovery/send-code", json={"email": "a@b.co"})
    assert r.status_code == 503


def test_password_recovery_happy_path(auth_client: TestClient) -> None:
    register_user(auth_client, "recover@example.com", "password12")
    r = auth_client.post(
        "/api/auth/password-recovery/send-code",
        json={"email": "recover@example.com"},
    )
    assert r.status_code == 200
    code = _latest_code("recover@example.com", VerificationPurpose.password_recovery)
    assert (
        auth_client.post(
            "/api/auth/password-recovery/verify-code",
            json={"email": "recover@example.com", "code": code},
        ).status_code
        == 200
    )
    complete = auth_client.post(
        "/api/auth/password-recovery/complete",
        json={
            "email": "recover@example.com",
            "code": code,
            "password": "newpassword12",
            "password_confirm": "newpassword12",
        },
    )
    assert complete.status_code == 200
    signin = auth_client.post(
        "/api/auth/signin",
        json={"email": "recover@example.com", "password": "newpassword12"},
    )
    assert signin.status_code == 200


def test_password_recovery_unknown_email_does_not_leak(auth_client: TestClient) -> None:
    r = auth_client.post(
        "/api/auth/password-recovery/send-code",
        json={"email": "missing@example.com"},
    )
    assert r.status_code == 200
    assert "verification code" in r.json()["message"].lower()


def test_password_recovery_oauth_only_user(auth_client: TestClient) -> None:
    with session_scope() as session:
        user = User(email="oauth@example.com", hashed_password=None, status=UserStatus.active)
        session.add(user)
        session.flush()
        session.add(
            UserIdentity(
                user_id=user.id,
                provider=AuthProvider.google,
                provider_subject=str(uuid4()),
            )
        )
    r = auth_client.post(
        "/api/auth/password-recovery/send-code",
        json={"email": "oauth@example.com"},
    )
    assert r.status_code == 200
    code = _latest_code("oauth@example.com", VerificationPurpose.password_recovery)
    assert (
        auth_client.post(
            "/api/auth/password-recovery/verify-code",
            json={"email": "oauth@example.com", "code": code},
        ).status_code
        == 200
    )
    complete = auth_client.post(
        "/api/auth/password-recovery/complete",
        json={
            "email": "oauth@example.com",
            "code": code,
            "password": "newpassword12",
            "password_confirm": "newpassword12",
        },
    )
    assert complete.status_code == 200
    signin = auth_client.post(
        "/api/auth/signin",
        json={"email": "oauth@example.com", "password": "newpassword12"},
    )
    assert signin.status_code == 200
    with session_scope() as session:
        identity = session.exec(
            select(UserIdentity).where(UserIdentity.user_id == user.id),
        ).first()
        assert identity is not None
        assert identity.provider == AuthProvider.google


def test_password_recovery_invalid_code(auth_client: TestClient) -> None:
    register_user(auth_client, "badrecover@example.com", "password12")
    assert (
        auth_client.post(
            "/api/auth/password-recovery/send-code",
            json={"email": "badrecover@example.com"},
        ).status_code
        == 200
    )
    r = auth_client.post(
        "/api/auth/password-recovery/verify-code",
        json={"email": "badrecover@example.com", "code": "BADBAD"},
    )
    assert r.status_code == 400
    assert r.json()["detail"]["code"] == ApiErrorCode.invalid_verification_code


def test_password_recovery_verification_code_cannot_be_reused(auth_client: TestClient) -> None:
    register_user(auth_client, "reuse-recover@example.com", "password12")
    assert (
        auth_client.post(
            "/api/auth/password-recovery/send-code",
            json={"email": "reuse-recover@example.com"},
        ).status_code
        == 200
    )
    code = _latest_code("reuse-recover@example.com", VerificationPurpose.password_recovery)
    verify_payload = {"email": "reuse-recover@example.com", "code": code}
    assert (
        auth_client.post(
            "/api/auth/password-recovery/verify-code",
            json=verify_payload,
        ).status_code
        == 200
    )
    verify_again = auth_client.post(
        "/api/auth/password-recovery/verify-code",
        json=verify_payload,
    )
    assert verify_again.status_code == 400
    assert verify_again.json()["detail"]["code"] == ApiErrorCode.invalid_verification_code

    complete_payload = {
        "email": "reuse-recover@example.com",
        "code": code,
        "password": "newpassword12",
        "password_confirm": "newpassword12",
    }
    assert (
        auth_client.post("/api/auth/password-recovery/complete", json=complete_payload).status_code
        == 200
    )
    complete_again = auth_client.post(
        "/api/auth/password-recovery/complete",
        json=complete_payload,
    )
    assert complete_again.status_code == 400
    assert complete_again.json()["detail"]["code"] == ApiErrorCode.invalid_verification_code

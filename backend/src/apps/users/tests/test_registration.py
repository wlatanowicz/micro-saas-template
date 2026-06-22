from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest
from fastapi.testclient import TestClient
from sqlmodel import select

from src.apps.users.api_errors import ApiErrorCode
from src.apps.users.models import VerificationCode, VerificationPurpose
from src.apps.users.tests.helpers import _latest_code, register_user
from src.utils.api_errors import CommonApiErrorCode
from src.utils.db import session_scope


def test_register_send_code_without_database(client: TestClient) -> None:
    r = client.post("/api/auth/register/send-code", json={"email": "a@b.co"})
    assert r.status_code == 503


def test_register_complete_without_database(client: TestClient) -> None:
    r = client.post(
        "/api/auth/register/complete",
        json={
            "email": "a@b.co",
            "code": "ABC123",
            "password": "password12",
            "password_confirm": "password12",
        },
    )
    assert r.status_code == 503


def test_registration_happy_path(auth_client: TestClient) -> None:
    data = register_user(auth_client, "new@example.com", "password12")
    assert data["token_type"] == "bearer"
    assert data["access_token"]
    assert data["user"]["email"] == "new@example.com"
    assert data["user"]["status"] == "active"


def test_registration_normalizes_email(auth_client: TestClient) -> None:
    assert (
        auth_client.post(
            "/api/auth/register/send-code",
            json={"email": "  Alice@Example.COM  "},
        ).status_code
        == 200
    )
    code = _latest_code("alice@example.com", VerificationPurpose.registration)
    assert (
        auth_client.post(
            "/api/auth/register/verify-code",
            json={"email": "alice@example.com", "code": code},
        ).status_code
        == 200
    )
    r = auth_client.post(
        "/api/auth/register/complete",
        json={
            "email": "alice@example.com",
            "code": code,
            "password": "password12",
            "password_confirm": "password12",
        },
    )
    assert r.status_code == 201
    assert r.json()["user"]["email"] == "alice@example.com"


def test_registration_duplicate_email_on_send_code(auth_client: TestClient) -> None:
    register_user(auth_client, "dup@example.com", "password12")
    r = auth_client.post("/api/auth/register/send-code", json={"email": "dup@example.com"})
    assert r.status_code == 409
    assert r.json()["detail"]["code"] == ApiErrorCode.email_already_registered


def test_registration_invalid_code(auth_client: TestClient) -> None:
    assert (
        auth_client.post(
            "/api/auth/register/send-code",
            json={"email": "bad@example.com"},
        ).status_code
        == 200
    )
    r = auth_client.post(
        "/api/auth/register/verify-code",
        json={"email": "bad@example.com", "code": "ZZZZZZ"},
    )
    assert r.status_code == 400
    assert r.json()["detail"]["code"] == ApiErrorCode.invalid_verification_code


def test_registration_complete_without_verify(auth_client: TestClient) -> None:
    assert (
        auth_client.post(
            "/api/auth/register/send-code",
            json={"email": "skip@example.com"},
        ).status_code
        == 200
    )
    code = _latest_code("skip@example.com", VerificationPurpose.registration)
    r = auth_client.post(
        "/api/auth/register/complete",
        json={
            "email": "skip@example.com",
            "code": code,
            "password": "password12",
            "password_confirm": "password12",
        },
    )
    assert r.status_code == 400
    assert r.json()["detail"]["code"] == ApiErrorCode.verification_code_not_verified


def test_registration_password_mismatch(auth_client: TestClient) -> None:
    assert (
        auth_client.post(
            "/api/auth/register/send-code",
            json={"email": "mismatch@example.com"},
        ).status_code
        == 200
    )
    code = _latest_code("mismatch@example.com", VerificationPurpose.registration)
    assert (
        auth_client.post(
            "/api/auth/register/verify-code",
            json={"email": "mismatch@example.com", "code": code},
        ).status_code
        == 200
    )
    r = auth_client.post(
        "/api/auth/register/complete",
        json={
            "email": "mismatch@example.com",
            "code": code,
            "password": "password12",
            "password_confirm": "password99",
        },
    )
    assert r.status_code == 400
    assert r.json()["detail"]["code"] == ApiErrorCode.passwords_do_not_match


def test_registration_verification_code_cannot_be_reused(auth_client: TestClient) -> None:
    assert (
        auth_client.post(
            "/api/auth/register/send-code",
            json={"email": "reuse@example.com"},
        ).status_code
        == 200
    )
    code = _latest_code("reuse@example.com", VerificationPurpose.registration)
    verify_payload = {"email": "reuse@example.com", "code": code}
    assert (
        auth_client.post("/api/auth/register/verify-code", json=verify_payload).status_code
        == 200
    )
    verify_again = auth_client.post("/api/auth/register/verify-code", json=verify_payload)
    assert verify_again.status_code == 400
    assert verify_again.json()["detail"]["code"] == ApiErrorCode.invalid_verification_code

    complete_payload = {
        "email": "reuse@example.com",
        "code": code,
        "password": "password12",
        "password_confirm": "password12",
    }
    assert auth_client.post("/api/auth/register/complete", json=complete_payload).status_code == 201
    complete_again = auth_client.post("/api/auth/register/complete", json=complete_payload)
    assert complete_again.status_code == 400
    assert complete_again.json()["detail"]["code"] == ApiErrorCode.invalid_verification_code


def test_registration_expired_code(auth_client: TestClient, monkeypatch) -> None:
    assert (
        auth_client.post(
            "/api/auth/register/send-code",
            json={"email": "expired@example.com"},
        ).status_code
        == 200
    )
    code = _latest_code("expired@example.com", VerificationPurpose.registration)
    with session_scope() as session:
        record = session.exec(
            select(VerificationCode).where(VerificationCode.email == "expired@example.com")
        ).first()
        assert record is not None
        record.valid_until = datetime.now(tz=UTC) - timedelta(minutes=1)
        session.add(record)
    r = auth_client.post(
        "/api/auth/register/verify-code",
        json={"email": "expired@example.com", "code": code},
    )
    assert r.status_code == 400
    assert r.json()["detail"]["code"] == ApiErrorCode.verification_code_expired


@pytest.mark.parametrize(
    ("payload", "substr"),
    [
        ({"email": "not-an-email"}, "email"),
        ({"email": "a@b.co", "code": "short"}, "code"),
    ],
)
def test_registration_validation_errors(
    auth_client: TestClient,
    payload: dict,
    substr: str,
) -> None:
    path = (
        "/api/auth/register/send-code"
        if "code" not in payload
        else "/api/auth/register/verify-code"
    )
    r = auth_client.post(path, json=payload)
    assert r.status_code == 422
    assert r.json()["detail"]["code"] == CommonApiErrorCode.request_validation_error

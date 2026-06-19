from __future__ import annotations

from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from src.apps.users.api_errors import ApiErrorCode
from src.apps.users.auth import create_access_token, hash_password
from src.apps.users.models import User, UserStatus
from src.apps.users.tests.helpers import register_user
from src.utils.db import session_scope


def test_signin_without_database(client: TestClient) -> None:
    r = client.post(
        "/api/auth/signin",
        json={"email": "a@b.co", "password": "password12"},
    )
    assert r.status_code == 503
    assert r.json()["detail"]["code"] == ApiErrorCode.database_not_configured


def test_me_without_database(client: TestClient) -> None:
    r = client.get("/api/auth/me")
    assert r.status_code == 503
    assert r.json()["detail"]["code"] == ApiErrorCode.database_not_configured


def test_auth_config_defaults(auth_client: TestClient) -> None:
    r = auth_client.get("/api/auth/config")
    assert r.status_code == 200
    body = r.json()
    assert body["password"] is True
    assert body["google"] is False
    assert body["facebook"] is False


def test_auth_config_reflects_env(auth_client: TestClient, monkeypatch) -> None:
    monkeypatch.setattr("src.apps.users.config.AUTH_PASSWORD_ENABLED", False)
    monkeypatch.setattr("src.apps.users.config.AUTH_GOOGLE_ENABLED", True)
    monkeypatch.setattr("src.apps.users.config.AUTH_FACEBOOK_ENABLED", True)
    r = auth_client.get("/api/auth/config")
    assert r.status_code == 200
    body = r.json()
    assert body["password"] is False
    assert body["google"] is True
    assert body["facebook"] is True


def test_register_send_code_password_disabled(auth_client: TestClient, monkeypatch) -> None:
    monkeypatch.setattr("src.apps.users.config.AUTH_PASSWORD_ENABLED", False)
    r = auth_client.post("/api/auth/register/send-code", json={"email": "a@b.co"})
    assert r.status_code == 403
    assert r.json()["detail"]["code"] == ApiErrorCode.auth_method_disabled


def test_signin_password_disabled(auth_client: TestClient, monkeypatch) -> None:
    monkeypatch.setattr("src.apps.users.config.AUTH_PASSWORD_ENABLED", False)
    r = auth_client.post(
        "/api/auth/signin",
        json={"email": "a@b.co", "password": "password12"},
    )
    assert r.status_code == 403
    assert r.json()["detail"]["code"] == ApiErrorCode.auth_method_disabled


def test_signin_success(auth_client: TestClient) -> None:
    register_user(auth_client, "login@example.com", "password12")
    r = auth_client.post(
        "/api/auth/signin",
        json={"email": "login@example.com", "password": "password12"},
    )
    assert r.status_code == 200
    data = r.json()
    assert data["token_type"] == "bearer"
    assert data["user"]["email"] == "login@example.com"


@pytest.mark.parametrize(
    ("email", "password"),
    [
        ("missing@example.com", "password12"),
        ("login@example.com", "wrong-password"),
    ],
)
def test_signin_invalid_credentials(
    auth_client: TestClient,
    email: str,
    password: str,
) -> None:
    register_user(auth_client, "login@example.com", "password12")
    r = auth_client.post("/api/auth/signin", json={"email": email, "password": password})
    assert r.status_code == 401
    assert r.json()["detail"]["code"] == ApiErrorCode.auth_invalid_credentials


def test_signin_inactive_forbidden(auth_client: TestClient) -> None:
    user = User(
        email="inactive@example.com",
        hashed_password=hash_password("password12"),
        status=UserStatus.inactive,
    )
    with session_scope() as session:
        session.add(user)

    r = auth_client.post(
        "/api/auth/signin",
        json={"email": "inactive@example.com", "password": "password12"},
    )
    assert r.status_code == 403
    assert r.json()["detail"]["code"] == ApiErrorCode.account_not_active


def test_me_success(auth_client: TestClient) -> None:
    signup = register_user(auth_client, "me@example.com", "password12")
    token = signup["access_token"]
    r = auth_client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 200
    assert r.json()["email"] == "me@example.com"
    assert r.json()["status"] == "active"


def test_me_missing_credentials(auth_client: TestClient) -> None:
    r = auth_client.get("/api/auth/me")
    assert r.status_code == 401
    assert r.json()["detail"]["code"] == ApiErrorCode.not_authenticated


def test_me_non_bearer_scheme(auth_client: TestClient) -> None:
    r = auth_client.get("/api/auth/me", headers={"Authorization": "Basic abc"})
    assert r.status_code == 401
    assert r.json()["detail"]["code"] == ApiErrorCode.not_authenticated


def test_me_invalid_token(auth_client: TestClient) -> None:
    r = auth_client.get("/api/auth/me", headers={"Authorization": "Bearer not-a-jwt"})
    assert r.status_code == 401
    assert r.json()["detail"]["code"] == ApiErrorCode.invalid_or_expired_token


def test_me_unknown_subject_claim(auth_client: TestClient) -> None:
    token = create_access_token(uuid4())
    r = auth_client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 401
    assert r.json()["detail"]["code"] == ApiErrorCode.user_not_found


def test_me_inactive_forbidden(auth_client: TestClient) -> None:
    user = User(
        email="blocked@example.com",
        hashed_password=hash_password("password12"),
        status=UserStatus.disabled,
    )
    user_id = user.id
    with session_scope() as session:
        session.add(user)

    token = create_access_token(user_id)
    r = auth_client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 403
    assert r.json()["detail"]["code"] == ApiErrorCode.account_not_active

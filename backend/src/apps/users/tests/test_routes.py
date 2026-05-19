from __future__ import annotations

from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.engine import Engine
from sqlmodel import Session

from src.apps.users.auth import create_access_token, hash_password
from src.apps.users.models import User, UserStatus


def test_signup_without_database(client: TestClient) -> None:
    r = client.post(
        "/api/auth/signup",
        json={"email": "a@b.co", "password": "password12"},
    )
    assert r.status_code == 503
    assert "database" in r.json()["detail"].lower()


def test_signin_without_database(client: TestClient) -> None:
    r = client.post(
        "/api/auth/signin",
        json={"email": "a@b.co", "password": "password12"},
    )
    assert r.status_code == 503
    assert "database" in r.json()["detail"].lower()


def test_me_without_database(client: TestClient) -> None:
    r = client.get("/api/auth/me")
    assert r.status_code == 503
    assert "database" in r.json()["detail"].lower()


@pytest.mark.parametrize(
    ("payload", "substr"),
    [
        ({"email": "not-an-email", "password": "password12"}, "email"),
        ({"email": "", "password": "password12"}, "email"),
        ({"email": "a@b.co", "password": "short"}, "password"),
    ],
)
def test_signup_validation_errors(auth_client: TestClient, payload: dict, substr: str) -> None:
    r = auth_client.post("/api/auth/signup", json=payload)
    assert r.status_code == 422
    body = r.json()
    assert substr in str(body).lower()


def test_signup_success_normalizes_email(auth_client: TestClient) -> None:
    r = auth_client.post(
        "/api/auth/signup",
        json={"email": "  Alice@Example.COM  ", "password": "password12"},
    )
    assert r.status_code == 201
    data = r.json()
    assert data["token_type"] == "bearer"
    assert data["access_token"]
    assert data["user"]["email"] == "alice@example.com"
    assert data["user"]["status"] == "active"


def test_signup_conflict_duplicate_email(auth_client: TestClient) -> None:
    body = {"email": "dup@example.com", "password": "password12"}
    assert auth_client.post("/api/auth/signup", json=body).status_code == 201
    r = auth_client.post("/api/auth/signup", json=body)
    assert r.status_code == 409
    assert r.json()["detail"] == "email already registered"


def test_signin_success(auth_client: TestClient) -> None:
    auth_client.post(
        "/api/auth/signup",
        json={"email": "login@example.com", "password": "password12"},
    )
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
    auth_client.post(
        "/api/auth/signup",
        json={"email": "login@example.com", "password": "password12"},
    )
    r = auth_client.post("/api/auth/signin", json={"email": email, "password": password})
    assert r.status_code == 401
    assert r.json()["detail"] == "Invalid email or password"


def test_signin_inactive_forbidden(sqlite_auth_engine: Engine, auth_client: TestClient) -> None:
    user = User(
        email="inactive@example.com",
        hashed_password=hash_password("password12"),
        status=UserStatus.inactive,
    )
    with Session(sqlite_auth_engine) as session:
        session.add(user)
        session.commit()

    r = auth_client.post(
        "/api/auth/signin",
        json={"email": "inactive@example.com", "password": "password12"},
    )
    assert r.status_code == 403
    assert r.json()["detail"] == "Account is not active"


def test_me_success(auth_client: TestClient) -> None:
    signup = auth_client.post(
        "/api/auth/signup",
        json={"email": "me@example.com", "password": "password12"},
    )
    token = signup.json()["access_token"]
    r = auth_client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 200
    assert r.json()["email"] == "me@example.com"
    assert r.json()["status"] == "active"


def test_me_missing_credentials(auth_client: TestClient) -> None:
    r = auth_client.get("/api/auth/me")
    assert r.status_code == 401
    assert r.json()["detail"] == "Not authenticated"


def test_me_non_bearer_scheme(auth_client: TestClient) -> None:
    r = auth_client.get("/api/auth/me", headers={"Authorization": "Basic abc"})
    assert r.status_code == 401
    assert r.json()["detail"] == "Not authenticated"


def test_me_invalid_token(auth_client: TestClient) -> None:
    r = auth_client.get("/api/auth/me", headers={"Authorization": "Bearer not-a-jwt"})
    assert r.status_code == 401
    assert r.json()["detail"] == "Invalid or expired token"


def test_me_unknown_subject_claim(sqlite_auth_engine: Engine, auth_client: TestClient) -> None:
    token = create_access_token(uuid4())
    r = auth_client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 401
    assert r.json()["detail"] == "User not found"


def test_me_inactive_forbidden(sqlite_auth_engine: Engine, auth_client: TestClient) -> None:
    user = User(
        email="blocked@example.com",
        hashed_password=hash_password("password12"),
        status=UserStatus.disabled,
    )
    with Session(sqlite_auth_engine) as session:
        session.add(user)
        session.commit()
        session.refresh(user)
        user_id = user.id

    token = create_access_token(user_id)
    r = auth_client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 403
    assert r.json()["detail"] == "Account is not active"

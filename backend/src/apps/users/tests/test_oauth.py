from __future__ import annotations

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient
from sqlmodel import select

from src.apps.users.api_errors import ApiErrorCode
from src.apps.users.auth import hash_password
from src.apps.users.models import AuthProvider, User, UserIdentity, UserStatus
from src.apps.users.oauth import (
    create_oauth_state,
    reset_oauth_registration,
    resolve_oauth_user,
    verify_oauth_state,
)
from src.apps.users.tests.helpers import register_user
from src.utils.db import session_scope


def test_create_and_verify_oauth_state(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "src.apps.users.config.JWT_SECRET",
        "test-jwt-secret-key-at-least-thirty-two-chars-for-local-and-ci",
    )
    state = create_oauth_state("google")
    verify_oauth_state(state, "google")


def test_verify_oauth_state_rejects_wrong_provider(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "src.apps.users.config.JWT_SECRET",
        "test-jwt-secret-key-at-least-thirty-two-chars-for-local-and-ci",
    )
    state = create_oauth_state("google")
    with pytest.raises(HTTPException) as exc_info:
        verify_oauth_state(state, "facebook")
    assert exc_info.value.detail["code"] == ApiErrorCode.invalid_oauth_state


def test_resolve_oauth_user_creates_user(postgres_integration) -> None:
    with session_scope() as session:
        user = resolve_oauth_user(
            session,
            AuthProvider.google,
            "google-sub-new",
            "oauth-new@example.com",
        )
        assert user.email == "oauth-new@example.com"
        assert user.hashed_password is None
        identity = session.exec(
            select(UserIdentity).where(UserIdentity.user_id == user.id),
        ).one()
        assert identity.provider == AuthProvider.google
        assert identity.provider_subject == "google-sub-new"


def test_resolve_oauth_user_auto_links_existing_email(auth_client: TestClient) -> None:
    register_user(auth_client, "link@example.com", "password12")
    with session_scope() as session:
        user = resolve_oauth_user(
            session,
            AuthProvider.google,
            "google-sub-link",
            "link@example.com",
        )
        assert user.email == "link@example.com"
        assert user.hashed_password is not None
        identities = session.exec(
            select(UserIdentity).where(UserIdentity.user_id == user.id),
        ).all()
        assert len(identities) == 1
        assert identities[0].provider_subject == "google-sub-link"


def test_resolve_oauth_user_returns_existing_identity(postgres_integration) -> None:
    with session_scope() as session:
        existing = User(
            email="existing@example.com",
            hashed_password=hash_password("password12"),
            status=UserStatus.active,
        )
        session.add(existing)
        session.flush()
        session.add(
            UserIdentity(
                user_id=existing.id,
                provider=AuthProvider.facebook,
                provider_subject="fb-99",
            ),
        )
        session.flush()
        user = resolve_oauth_user(
            session,
            AuthProvider.facebook,
            "fb-99",
            "existing@example.com",
        )
        assert user.id == existing.id


def test_google_callback_creates_user(auth_client: TestClient, monkeypatch) -> None:
    monkeypatch.setattr("src.apps.users.config.AUTH_GOOGLE_ENABLED", True)
    monkeypatch.setattr("src.apps.users.config.AUTH_GOOGLE_CLIENT_ID", "test-google-id")
    monkeypatch.setattr("src.apps.users.config.AUTH_GOOGLE_CLIENT_SECRET", "test-google-secret")
    monkeypatch.setattr("src.apps.users.config.AUTH_FRONTEND_URL", "http://localhost:5173")
    reset_oauth_registration()

    from src.apps.users import oauth as oauth_mod

    async def fake_authorize_access_token(request):  # noqa: ARG001
        return {"userinfo": {"sub": "g-callback-1", "email": "callback@example.com"}}

    class FakeClient:
        authorize_access_token = staticmethod(fake_authorize_access_token)

    monkeypatch.setattr(
        oauth_mod.oauth,
        "create_client",
        lambda name: FakeClient() if name == "google" else None,
    )

    state = create_oauth_state("google")
    r = auth_client.get(
        f"/api/auth/google/callback?code=fake&state={state}",
        follow_redirects=False,
    )
    assert r.status_code == 302
    assert r.headers["location"].startswith("http://localhost:5173#access_token=")

    with session_scope() as session:
        user = session.exec(
            select(User).where(User.email == "callback@example.com"),
        ).first()
        assert user is not None
        assert user.hashed_password is None


def test_google_start_disabled(auth_client: TestClient, monkeypatch) -> None:
    monkeypatch.setattr("src.apps.users.config.AUTH_GOOGLE_ENABLED", False)
    r = auth_client.get("/api/auth/google", follow_redirects=False)
    assert r.status_code == 403
    assert r.json()["detail"]["code"] == ApiErrorCode.auth_method_disabled


def test_google_start_missing_credentials(auth_client: TestClient, monkeypatch) -> None:
    monkeypatch.setattr("src.apps.users.config.AUTH_GOOGLE_ENABLED", True)
    monkeypatch.setattr("src.apps.users.config.AUTH_GOOGLE_CLIENT_ID", None)
    monkeypatch.setattr("src.apps.users.config.AUTH_GOOGLE_CLIENT_SECRET", None)
    r = auth_client.get("/api/auth/google", follow_redirects=False)
    assert r.status_code == 503

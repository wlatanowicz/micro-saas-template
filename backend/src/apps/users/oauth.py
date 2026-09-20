from __future__ import annotations

import secrets
from datetime import UTC, datetime, timedelta
from urllib.parse import parse_qsl, urlencode, urlparse, urlunparse

import jwt
from authlib.integrations.starlette_client import OAuth
from fastapi import HTTPException, Request
from fastapi.responses import RedirectResponse
from sqlmodel import Session, select

from src.apps.users import config
from src.apps.users.api_errors import ApiErrorCode
from src.apps.users.auth import create_access_token, normalize_email
from src.apps.users.guards import AuthProviderName
from src.apps.users.models import AuthProvider, User, UserIdentity, UserStatus
from src.utils.api_errors import CommonApiErrorCode, api_error_code_from_detail, raise_api_error

oauth = OAuth()
_registered = False

STATE_TTL_MINUTES = 10


def _register_oauth_clients() -> None:
    if config.AUTH_GOOGLE_CLIENT_ID and config.AUTH_GOOGLE_CLIENT_SECRET:
        oauth.register(
            name="google",
            client_id=config.AUTH_GOOGLE_CLIENT_ID,
            client_secret=config.AUTH_GOOGLE_CLIENT_SECRET,
            server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",
            client_kwargs={"scope": "openid email profile"},
        )
    if config.AUTH_FACEBOOK_APP_ID and config.AUTH_FACEBOOK_APP_SECRET:
        oauth.register(
            name="facebook",
            client_id=config.AUTH_FACEBOOK_APP_ID,
            client_secret=config.AUTH_FACEBOOK_APP_SECRET,
            authorize_url="https://www.facebook.com/v21.0/dialog/oauth",
            access_token_url="https://graph.facebook.com/v21.0/oauth/access_token",
            api_base_url="https://graph.facebook.com/v21.0/",
            client_kwargs={"scope": "email public_profile"},
        )


def ensure_oauth_clients_registered() -> None:
    global _registered
    if not _registered:
        _register_oauth_clients()
        _registered = True


def reset_oauth_registration() -> None:
    """Reset cached OAuth client registration (for tests)."""
    global _registered
    _registered = False
    oauth._clients.clear()


def create_oauth_state(provider: AuthProviderName, redirect_uri: str | None = None) -> str:
    secret = config.JWT_SECRET
    if not secret:
        msg = "JWT_SECRET is not configured"
        raise RuntimeError(msg)
    expire = datetime.now(UTC) + timedelta(minutes=STATE_TTL_MINUTES)
    payload: dict[str, object] = {
        "purpose": "oauth_state",
        "provider": provider,
        "nonce": secrets.token_urlsafe(16),
        "exp": expire,
    }
    if redirect_uri:
        payload["redirect_uri"] = redirect_uri
    return jwt.encode(
        payload,
        secret,
        algorithm="HS256",
    )


def verify_oauth_state(state: str, provider: AuthProviderName) -> str | None:
    secret = config.JWT_SECRET
    if not secret:
        msg = "JWT_SECRET is not configured"
        raise RuntimeError(msg)
    try:
        payload = jwt.decode(state, secret, algorithms=["HS256"])
    except jwt.PyJWTError:
        raise_api_error(
            ApiErrorCode.invalid_oauth_state,
            "invalid oauth state",
            status_code=400,
        )
    if payload.get("purpose") != "oauth_state" or payload.get("provider") != provider:
        raise_api_error(
            ApiErrorCode.invalid_oauth_state,
            "invalid oauth state",
            status_code=400,
        )
    redirect_uri = payload.get("redirect_uri")
    if isinstance(redirect_uri, str) and redirect_uri:
        return redirect_uri
    return None


def is_allowed_oauth_client_redirect(uri: str) -> bool:
    parsed = urlparse(uri)
    if not parsed.scheme:
        return False
    scheme = parsed.scheme.lower()
    if scheme in {"http", "https"}:
        frontend = urlparse(config.AUTH_FRONTEND_URL)
        return (
            scheme == frontend.scheme.lower()
            and parsed.netloc.lower() == frontend.netloc.lower()
        )
    return scheme in {s.lower() for s in config.AUTH_OAUTH_NATIVE_SCHEMES}


def _is_native_redirect(uri: str) -> bool:
    return urlparse(uri).scheme.lower() not in {"http", "https"}


def build_client_redirect(redirect_uri: str | None, params: dict[str, str]) -> str:
    target = redirect_uri or config.AUTH_FRONTEND_URL
    parsed = urlparse(target)
    if _is_native_redirect(target):
        existing = dict(parse_qsl(parsed.query, keep_blank_values=True))
        existing.update(params)
        return urlunparse(parsed._replace(query=urlencode(existing), fragment=""))
    return urlunparse(parsed._replace(fragment=urlencode(params)))


def build_redirect_uri(request: Request, callback_name: str) -> str:
    return str(request.url_for(callback_name))


def oauth_success_redirect(user: User, redirect_uri: str | None = None) -> RedirectResponse:
    token = create_access_token(user.id)
    return RedirectResponse(
        url=build_client_redirect(
            redirect_uri,
            {"access_token": token, "token_type": "bearer"},
        ),
        status_code=302,
    )


def oauth_error_redirect(code: str, redirect_uri: str | None = None) -> RedirectResponse:
    return RedirectResponse(
        url=build_client_redirect(redirect_uri, {"auth_error_code": code}),
        status_code=302,
    )


def _oauth_error_redirect_from_exception(
    exc: HTTPException,
    redirect_uri: str | None = None,
) -> RedirectResponse:
    code = api_error_code_from_detail(exc.detail)
    if code is None:
        code = CommonApiErrorCode.request_validation_error
    return oauth_error_redirect(code, redirect_uri)


def resolve_oauth_user(
    session: Session,
    provider: AuthProvider,
    subject: str,
    email: str,
) -> User:
    normalized_email = normalize_email(email)
    identity = session.exec(
        select(UserIdentity).where(
            UserIdentity.provider == provider,
            UserIdentity.provider_subject == subject,
        ),
    ).first()
    if identity is not None:
        user = session.get(User, identity.user_id)
        if user is None:
            raise_api_error(
                ApiErrorCode.identity_references_missing_user,
                "identity references missing user",
                status_code=500,
            )
        if user.status != UserStatus.active:
            raise_api_error(
                ApiErrorCode.account_not_active,
                "Account is not active",
                status_code=403,
            )
        return user

    user = session.exec(select(User).where(User.email == normalized_email)).first()
    if user is not None:
        session.add(
            UserIdentity(
                user_id=user.id,
                provider=provider,
                provider_subject=subject,
            ),
        )
        session.flush()
        if user.status != UserStatus.active:
            raise_api_error(
                ApiErrorCode.account_not_active,
                "Account is not active",
                status_code=403,
            )
        return user

    user = User(email=normalized_email, hashed_password=None, status=UserStatus.active)
    session.add(user)
    session.flush()
    session.refresh(user)
    session.add(
        UserIdentity(
            user_id=user.id,
            provider=provider,
            provider_subject=subject,
        ),
    )
    session.flush()
    return user


async def authorize_redirect(
    request: Request,
    provider: AuthProviderName,
    callback_name: str,
) -> RedirectResponse:
    ensure_oauth_clients_registered()
    requested = request.query_params.get("redirect_uri")
    client_redirect: str | None = None
    if requested:
        if not is_allowed_oauth_client_redirect(requested):
            raise_api_error(
                CommonApiErrorCode.request_validation_error,
                "invalid oauth redirect_uri",
                status_code=400,
            )
        client_redirect = requested
    state = create_oauth_state(provider, client_redirect)
    redirect_uri = build_redirect_uri(request, callback_name)
    client = oauth.create_client(provider)
    if client is None:
        raise_api_error(
            ApiErrorCode.oauth_provider_not_configured,
            f"{provider} oauth client not configured",
            status_code=503,
            params={"provider": provider},
        )
    return await client.authorize_redirect(request, redirect_uri, state=state)


async def complete_google_callback(request: Request, session: Session) -> RedirectResponse:
    ensure_oauth_clients_registered()
    state = request.query_params.get("state", "")
    try:
        client_redirect = verify_oauth_state(state, "google")
    except HTTPException as exc:
        return _oauth_error_redirect_from_exception(exc)
    client = oauth.create_client("google")
    if client is None:
        return oauth_error_redirect(ApiErrorCode.oauth_provider_not_configured, client_redirect)
    try:
        token = await client.authorize_access_token(request)
    except Exception:
        return oauth_error_redirect(ApiErrorCode.oauth_authorization_failed, client_redirect)
    userinfo = token.get("userinfo")
    if not userinfo:
        return oauth_error_redirect(ApiErrorCode.oauth_profile_missing, client_redirect)
    subject = userinfo.get("sub")
    email = userinfo.get("email")
    if not subject or not email:
        return oauth_error_redirect(ApiErrorCode.oauth_email_not_available, client_redirect)
    try:
        user = resolve_oauth_user(session, AuthProvider.google, str(subject), str(email))
    except HTTPException as exc:
        return _oauth_error_redirect_from_exception(exc, client_redirect)
    return oauth_success_redirect(user, client_redirect)


async def complete_facebook_callback(request: Request, session: Session) -> RedirectResponse:
    ensure_oauth_clients_registered()
    state = request.query_params.get("state", "")
    try:
        client_redirect = verify_oauth_state(state, "facebook")
    except HTTPException as exc:
        return _oauth_error_redirect_from_exception(exc)
    client = oauth.create_client("facebook")
    if client is None:
        return oauth_error_redirect(ApiErrorCode.oauth_provider_not_configured, client_redirect)
    try:
        token = await client.authorize_access_token(request)
        resp = await client.get("me?fields=id,email", token=token)
        profile = resp.json()
    except Exception:
        return oauth_error_redirect(ApiErrorCode.oauth_authorization_failed, client_redirect)
    subject = profile.get("id")
    email = profile.get("email")
    if not subject or not email:
        return oauth_error_redirect(ApiErrorCode.oauth_email_not_available, client_redirect)
    try:
        user = resolve_oauth_user(session, AuthProvider.facebook, str(subject), str(email))
    except HTTPException as exc:
        return _oauth_error_redirect_from_exception(exc, client_redirect)
    return oauth_success_redirect(user, client_redirect)

from __future__ import annotations

from typing import Literal

from fastapi import HTTPException

from src.apps.users import config

AuthMethod = Literal["password", "google", "facebook"]
AuthProviderName = Literal["google", "facebook"]


def require_method_enabled(method: AuthMethod) -> None:
    enabled = {
        "password": config.AUTH_PASSWORD_ENABLED,
        "google": config.AUTH_GOOGLE_ENABLED,
        "facebook": config.AUTH_FACEBOOK_ENABLED,
    }[method]
    if not enabled:
        raise HTTPException(
            status_code=403,
            detail=f"{method} authentication is disabled",
        )


def ensure_provider_configured(provider: AuthProviderName) -> None:
    if provider == "google":
        if config.AUTH_GOOGLE_CLIENT_ID and config.AUTH_GOOGLE_CLIENT_SECRET:
            return
        raise HTTPException(
            status_code=503,
            detail=(
                "google auth not configured "
                "(set AUTH_GOOGLE_CLIENT_ID and AUTH_GOOGLE_CLIENT_SECRET)"
            ),
        )
    if provider == "facebook":
        if config.AUTH_FACEBOOK_APP_ID and config.AUTH_FACEBOOK_APP_SECRET:
            return
        raise HTTPException(
            status_code=503,
            detail=(
                "facebook auth not configured "
                "(set AUTH_FACEBOOK_APP_ID and AUTH_FACEBOOK_APP_SECRET)"
            ),
        )

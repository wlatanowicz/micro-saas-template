from __future__ import annotations

from typing import Literal

from src.apps.users import config
from src.apps.users.api_errors import ApiErrorCode
from src.utils.api_errors import raise_api_error

AuthMethod = Literal["password", "google", "facebook"]
AuthProviderName = Literal["google", "facebook"]


def require_method_enabled(method: AuthMethod) -> None:
    enabled = {
        "password": config.AUTH_PASSWORD_ENABLED,
        "google": config.AUTH_GOOGLE_ENABLED,
        "facebook": config.AUTH_FACEBOOK_ENABLED,
    }[method]
    if not enabled:
        raise_api_error(
            ApiErrorCode.auth_method_disabled,
            f"{method} authentication is disabled",
            status_code=403,
            params={"method": method},
        )


def ensure_provider_configured(provider: AuthProviderName) -> None:
    if provider == "google":
        if config.AUTH_GOOGLE_CLIENT_ID and config.AUTH_GOOGLE_CLIENT_SECRET:
            return
        raise_api_error(
            ApiErrorCode.oauth_provider_not_configured,
            (
                "google auth not configured "
                "(set AUTH_GOOGLE_CLIENT_ID and AUTH_GOOGLE_CLIENT_SECRET)"
            ),
            status_code=503,
            params={"provider": provider},
        )
    if provider == "facebook":
        if config.AUTH_FACEBOOK_APP_ID and config.AUTH_FACEBOOK_APP_SECRET:
            return
        raise_api_error(
            ApiErrorCode.oauth_provider_not_configured,
            (
                "facebook auth not configured "
                "(set AUTH_FACEBOOK_APP_ID and AUTH_FACEBOOK_APP_SECRET)"
            ),
            status_code=503,
            params={"provider": provider},
        )

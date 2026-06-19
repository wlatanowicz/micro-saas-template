from __future__ import annotations

from enum import StrEnum


class ApiErrorCode(StrEnum):
    database_not_configured = "database_not_configured"
    auth_not_configured = "auth_not_configured"
    auth_invalid_credentials = "auth_invalid_credentials"
    account_not_active = "account_not_active"
    not_authenticated = "not_authenticated"
    invalid_or_expired_token = "invalid_or_expired_token"
    invalid_token = "invalid_token"
    user_not_found = "user_not_found"
    auth_method_disabled = "auth_method_disabled"
    oauth_provider_not_configured = "oauth_provider_not_configured"
    verification_code_expired = "verification_code_expired"
    invalid_verification_code = "invalid_verification_code"
    email_already_registered = "email_already_registered"
    passwords_do_not_match = "passwords_do_not_match"
    auth_password_too_short = "auth_password_too_short"
    verification_code_not_verified = "verification_code_not_verified"
    invalid_oauth_state = "invalid_oauth_state"
    identity_references_missing_user = "identity_references_missing_user"
    oauth_authorization_failed = "oauth_authorization_failed"
    oauth_profile_missing = "oauth_profile_missing"
    oauth_email_not_available = "oauth_email_not_available"

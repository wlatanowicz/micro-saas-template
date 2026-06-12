from __future__ import annotations

import os

from src.apps.notifications.config import NOTIFICATIONS_TRANSPORT
from src.apps.notifications.transports import local_eml, ses
from src.utils.env import ConfigurationError


def send_email(
    *,
    to: str,
    subject: str,
    plain_body: str,
    html_body: str,
    purpose: str = "message",
) -> None:
    transport = (NOTIFICATIONS_TRANSPORT or "local").lower()
    if transport == "local":
        if os.environ.get("AWS_LAMBDA_FUNCTION_NAME"):
            msg = (
                "NOTIFICATIONS_TRANSPORT=local is not supported on AWS Lambda; "
                "set NOTIFICATIONS_TRANSPORT=ses"
            )
            raise ConfigurationError(msg)
        local_eml.write_eml(
            to=to,
            subject=subject,
            plain_body=plain_body,
            html_body=html_body,
            purpose=purpose,
        )
        return
    if transport == "ses":
        ses.send_via_ses(
            to=to,
            subject=subject,
            plain_body=plain_body,
            html_body=html_body,
        )
        return
    msg = f"unsupported NOTIFICATIONS_TRANSPORT: {transport}"
    raise ConfigurationError(msg)

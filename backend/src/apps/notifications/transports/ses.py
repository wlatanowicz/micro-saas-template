from __future__ import annotations

from src.apps.notifications.config import NOTIFICATIONS_FROM_EMAIL
from src.utils.env import ConfigurationError


def send_via_ses(*, to: str, subject: str, plain_body: str, html_body: str) -> None:
    import boto3

    if not NOTIFICATIONS_FROM_EMAIL:
        msg = "NOTIFICATIONS_FROM_EMAIL is required when NOTIFICATIONS_TRANSPORT=ses"
        raise ConfigurationError(msg)
    client = boto3.client("ses")
    client.send_email(
        Source=NOTIFICATIONS_FROM_EMAIL,
        Destination={"ToAddresses": [to]},
        Message={
            "Subject": {"Data": subject, "Charset": "UTF-8"},
            "Body": {
                "Text": {"Data": plain_body, "Charset": "UTF-8"},
                "Html": {"Data": html_body, "Charset": "UTF-8"},
            },
        },
    )

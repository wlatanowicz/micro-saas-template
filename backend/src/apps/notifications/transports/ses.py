from __future__ import annotations

import logging
import os

from src.apps.notifications.config import NOTIFICATIONS_FROM_EMAIL
from src.utils.env import ConfigurationError

logger = logging.getLogger(__name__)


def send_via_ses(*, to: str, subject: str, plain_body: str, html_body: str) -> None:
    import boto3
    from botocore.exceptions import ClientError

    if not NOTIFICATIONS_FROM_EMAIL:
        msg = "NOTIFICATIONS_FROM_EMAIL is required when NOTIFICATIONS_TRANSPORT=ses"
        raise ConfigurationError(msg)
    region = os.environ.get("AWS_REGION") or os.environ.get("AWS_DEFAULT_REGION")
    if not region:
        msg = "AWS_REGION is not set; cannot create SES client"
        raise ConfigurationError(msg)
    client = boto3.client("ses", region_name=region)
    try:
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
    except ClientError:
        logger.exception(
            "SES SendEmail failed (from=%s, to=%s, region=%s)",
            NOTIFICATIONS_FROM_EMAIL,
            to,
            region,
        )
        raise

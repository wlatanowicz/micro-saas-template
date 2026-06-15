from __future__ import annotations

import json
import logging
import os
from typing import Any

logger = logging.getLogger(__name__)


def send_message(*, queue_url: str, payload: dict[str, Any]) -> str:
    import boto3

    region = os.environ.get("AWS_REGION") or os.environ.get("AWS_DEFAULT_REGION")
    if not region:
        msg = "AWS_REGION is not set; cannot create SQS client"
        raise RuntimeError(msg)
    client = boto3.client("sqs", region_name=region)
    try:
        response = client.send_message(
            QueueUrl=queue_url,
            MessageBody=json.dumps(payload),
        )
    except Exception:
        logger.exception("SQS SendMessage failed (queue_url=%s)", queue_url)
        raise
    message_id = response.get("MessageId")
    if not isinstance(message_id, str):
        msg = "SQS SendMessage response did not include MessageId"
        raise RuntimeError(msg)
    return message_id

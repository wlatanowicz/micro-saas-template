from __future__ import annotations

import re
from datetime import UTC, datetime
from email.message import EmailMessage
from pathlib import Path

from src.apps.notifications.config import NOTIFICATIONS_EML_DIR, NOTIFICATIONS_FROM_EMAIL


def _sanitize_filename_part(value: str) -> str:
    return re.sub(r"[^a-zA-Z0-9._-]+", "_", value)[:80]


def write_eml(
    *,
    to: str,
    subject: str,
    plain_body: str,
    html_body: str,
    purpose: str = "message",
) -> Path:
    outbox = Path(NOTIFICATIONS_EML_DIR or "")
    outbox.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(tz=UTC).strftime("%Y%m%dT%H%M%S%fZ")
    filename = f"{timestamp}_{purpose}_{_sanitize_filename_part(to)}.eml"
    path = outbox / filename

    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = NOTIFICATIONS_FROM_EMAIL or "noreply@localhost"
    msg["To"] = to
    msg.set_content(plain_body)
    msg.add_alternative(html_body, subtype="html")
    path.write_bytes(msg.as_bytes())
    return path

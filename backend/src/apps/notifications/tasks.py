from __future__ import annotations

from src import background
from src.apps.notifications.service import deliver_templated_email


@background.task(queue="MESSAGES")
def send_templated_email_task(
    template_base: str,
    *,
    to: str,
    context: dict[str, str],
    purpose: str | None = None,
) -> None:
    deliver_templated_email(
        template_base,
        to=to,
        context=context,
        purpose=purpose,
    )

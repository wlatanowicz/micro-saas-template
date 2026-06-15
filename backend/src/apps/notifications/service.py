from __future__ import annotations

from src.apps.notifications import sender, templates

_TEMPLATE_SUBJECTS = {
    "registration_code": "Your registration code",
    "password_recovery_code": "Your password recovery code",
}


def deliver_templated_email(
    template_base: str,
    *,
    to: str,
    context: dict[str, str],
    purpose: str | None = None,
) -> None:
    plain_body = templates.render_template(template_base, kind="plain", context=context)
    html_body = templates.render_template(template_base, kind="html", context=context)
    subject = _TEMPLATE_SUBJECTS.get(template_base, "Notification")
    sender.send_email(
        to=to,
        subject=subject,
        plain_body=plain_body,
        html_body=html_body,
        purpose=purpose or template_base,
    )


def send_templated_email(
    template_base: str,
    *,
    to: str,
    context: dict[str, str],
    purpose: str | None = None,
) -> None:
    from src.apps.notifications.tasks import send_templated_email_task

    send_templated_email_task.enqueue(
        template_base,
        to=to,
        context=context,
        purpose=purpose,
    )

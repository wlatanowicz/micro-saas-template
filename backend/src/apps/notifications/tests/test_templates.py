from __future__ import annotations

import pytest
from src.apps.notifications.templates import render_template


def test_registration_plain_template_substitutes() -> None:
    body = render_template(
        "registration_code",
        kind="plain",
        context={"email": "a@b.co", "code": "ABC123", "valid_minutes": "30"},
    )
    assert "ABC123" in body
    assert "30" in body


def test_password_recovery_html_template_substitutes() -> None:
    body = render_template(
        "password_recovery_code",
        kind="html",
        context={"email": "a@b.co", "code": "XYZ789", "valid_minutes": "30"},
    )
    assert "XYZ789" in body
    assert "<strong>" in body


def test_missing_template_raises() -> None:
    with pytest.raises(FileNotFoundError, match="template not found"):
        render_template("missing_template", kind="plain", context={})

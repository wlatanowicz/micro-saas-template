from __future__ import annotations

from pathlib import Path

from src.apps.notifications.transports import local_eml


def test_write_eml_creates_file(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr("src.apps.notifications.config.NOTIFICATIONS_EML_DIR", str(tmp_path))
    monkeypatch.setattr(
        "src.apps.notifications.config.NOTIFICATIONS_FROM_EMAIL",
        "noreply@test.local",
    )
    path = local_eml.write_eml(
        to="user@example.com",
        subject="Test",
        plain_body="plain",
        html_body="<p>html</p>",
        purpose="registration",
    )
    assert path.is_file()
    content = path.read_text(encoding="utf-8")
    assert "user@example.com" in content
    assert "plain" in content
    assert "html" in content

from __future__ import annotations

from unittest.mock import MagicMock

import pytest
from src.apps.notifications import service
from src.apps.notifications.tasks import send_templated_email_task


def test_send_templated_email_enqueues_scheduled_task(monkeypatch: pytest.MonkeyPatch) -> None:
    mock_enqueue = MagicMock()
    monkeypatch.setattr(send_templated_email_task, "enqueue", mock_enqueue)
    service.send_templated_email(
        "registration_code",
        to="user@example.com",
        context={"email": "user@example.com", "code": "ABC123", "valid_minutes": "30"},
        purpose="registration",
    )
    mock_enqueue.assert_called_once_with(
        "registration_code",
        to="user@example.com",
        context={"email": "user@example.com", "code": "ABC123", "valid_minutes": "30"},
        purpose="registration",
    )


def test_send_templated_email_task_delivers_email(monkeypatch: pytest.MonkeyPatch) -> None:
    mock_deliver = MagicMock()
    monkeypatch.setattr("src.apps.notifications.tasks.deliver_templated_email", mock_deliver)
    send_templated_email_task(
        "password_recovery_code",
        to="user@example.com",
        context={"email": "user@example.com", "code": "XYZ789", "valid_minutes": "30"},
        purpose="password_recovery",
    )
    mock_deliver.assert_called_once_with(
        "password_recovery_code",
        to="user@example.com",
        context={"email": "user@example.com", "code": "XYZ789", "valid_minutes": "30"},
        purpose="password_recovery",
    )

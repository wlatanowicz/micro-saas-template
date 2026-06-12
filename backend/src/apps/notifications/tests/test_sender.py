import pytest
from src.apps.notifications import sender
from src.utils.env import ConfigurationError


def test_local_transport_rejected_on_lambda(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("src.apps.notifications.config.NOTIFICATIONS_TRANSPORT", "local")
    monkeypatch.setenv("AWS_LAMBDA_FUNCTION_NAME", "micro-saas-app-prod-api")
    with pytest.raises(ConfigurationError, match="not supported on AWS Lambda"):
        sender.send_email(
            to="a@b.co",
            subject="Test",
            plain_body="plain",
            html_body="<p>html</p>",
        )

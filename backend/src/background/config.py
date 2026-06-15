from __future__ import annotations

from src.utils.env import ConfigurationError, env_str

BACKGROUND_TRANSPORT = env_str("BACKGROUND_TRANSPORT", default="sync")


def queue_url(queue_name: str) -> str:
    env_name = f"BACKGROUND_QUEUE_{queue_name}_URL"
    url = env_str(env_name)
    if not url:
        msg = f"{env_name} is required when BACKGROUND_TRANSPORT=sqs"
        raise ConfigurationError(msg)
    return url

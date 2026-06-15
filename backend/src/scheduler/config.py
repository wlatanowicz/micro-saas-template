from __future__ import annotations

from src.utils.env import ConfigurationError, env_str

SCHEDULER_TRANSPORT = env_str("SCHEDULER_TRANSPORT", default="sync")


def queue_url(queue_name: str) -> str:
    env_name = f"SCHEDULER_QUEUE_{queue_name}_URL"
    url = env_str(env_name)
    if not url:
        msg = f"{env_name} is required when SCHEDULER_TRANSPORT=sqs"
        raise ConfigurationError(msg)
    return url

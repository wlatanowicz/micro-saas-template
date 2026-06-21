from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Any

from src.scheduler.registry import RegisteredTask


@dataclass(frozen=True, slots=True)
class TaskPayload:
    function_path: str
    args: list[Any]
    kwargs: dict[str, Any]
    created_at: datetime
    expire_seconds: float | None = None

    @classmethod
    def for_task(
        cls,
        registered: RegisteredTask,
        *args: Any,
        created_at: datetime | None = None,
        **kwargs: Any,
    ) -> TaskPayload:
        queued_at = created_at if created_at is not None else datetime.now(tz=UTC)
        expire_seconds = (
            registered.expire.total_seconds() if registered.expire is not None else None
        )
        return cls(
            function_path=registered.function_path,
            args=list(args),
            kwargs=kwargs,
            created_at=queued_at,
            expire_seconds=expire_seconds,
        )

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> TaskPayload:
        args = data.get("args", [])
        kwargs = data.get("kwargs", {})
        if not isinstance(args, list):
            msg = f"payload args must be a list, got {type(args).__name__}"
            raise TypeError(msg)
        if not isinstance(kwargs, dict):
            msg = f"payload kwargs must be a dict, got {type(kwargs).__name__}"
            raise TypeError(msg)
        created_at = _parse_created_at(data["created_at"])
        expire_raw = data.get("expire_seconds")
        expire_seconds = float(expire_raw) if expire_raw is not None else None
        return cls(
            function_path=data["function_path"],
            args=args,
            kwargs=kwargs,
            created_at=created_at,
            expire_seconds=expire_seconds,
        )

    def to_dict(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "function_path": self.function_path,
            "args": self.args,
            "kwargs": self.kwargs,
            "created_at": self.created_at.isoformat(),
        }
        if self.expire_seconds is not None:
            payload["expire_seconds"] = self.expire_seconds
        return payload

    def is_expired(self, *, now: datetime | None = None) -> bool:
        if self.expire_seconds is None:
            return False
        current = now if now is not None else datetime.now(tz=UTC)
        expires_at = self.created_at + timedelta(seconds=self.expire_seconds)
        return current >= expires_at


def _parse_created_at(value: object) -> datetime:
    if isinstance(value, datetime):
        created_at = value
    elif isinstance(value, str):
        created_at = datetime.fromisoformat(value)
    else:
        msg = f"created_at must be a datetime or ISO string, got {type(value).__name__}"
        raise TypeError(msg)
    if created_at.tzinfo is None:
        return created_at.replace(tzinfo=UTC)
    return created_at

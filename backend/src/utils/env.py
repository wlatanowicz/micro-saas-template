from __future__ import annotations

import os
from collections.abc import Callable
from decimal import Decimal
from typing import Any, TypeVar

_T = TypeVar("_T")

_NOVALUE = object()


class ConfigurationError(Exception):
    """Raised when a required environment variable is missing or invalid."""


def _raw_value(name: str) -> str | None:
    raw = os.environ.get(name)
    if raw is None:
        return None
    stripped = raw.strip()
    return stripped or None


def _resolve_default(
    name: str,
    *,
    default: Any,
    expected_type: type[_T],
) -> _T | None:
    if default is _NOVALUE:
        raise ConfigurationError(f"{name} is required")
    if default is not None and not isinstance(default, expected_type):
        msg = (
            f"{name}: default must be {expected_type.__name__} or None, "
            f"got {type(default).__name__}"
        )
        raise ConfigurationError(msg)
    return default


def env_str(name: str, *, default: str | None | object = _NOVALUE) -> str | None:
    value = _raw_value(name)
    if value is not None:
        return value
    return _resolve_default(name, default=default, expected_type=str)


_TRUTHY = frozenset({"1", "true", "yes", "on"})


def env_bool(name: str, *, default: bool | None | object = _NOVALUE) -> bool | None:
    value = _raw_value(name)
    if value is not None:
        return value.lower() in _TRUTHY
    return _resolve_default(name, default=default, expected_type=bool)


def env_int(name: str, *, default: int | None | object = _NOVALUE) -> int | None:
    value = _raw_value(name)
    if value is not None:
        try:
            return int(value)
        except ValueError as e:
            raise ConfigurationError(f"{name} must be an integer") from e
    return _resolve_default(name, default=default, expected_type=int)


def env_float(name: str, *, default: float | None | object = _NOVALUE) -> float | None:
    value = _raw_value(name)
    if value is not None:
        try:
            return float(value)
        except ValueError as e:
            raise ConfigurationError(f"{name} must be a float") from e
    return _resolve_default(name, default=default, expected_type=float)


def env_decimal(
    name: str,
    *,
    default: Decimal | None | object = _NOVALUE,
) -> Decimal | None:
    value = _raw_value(name)
    if value is not None:
        try:
            return Decimal(value)
        except Exception as e:
            raise ConfigurationError(f"{name} must be a decimal") from e
    return _resolve_default(name, default=default, expected_type=Decimal)


def env_list(
    name: str,
    *,
    default: list | object = _NOVALUE,
    cast: Callable[[str], Any] = str,
    separator: str = ",",
    strip: bool = True,
) -> list | None:
    value = _raw_value(name)
    if value is not None:
        parts = value.split(separator)
        if strip:
            parts = [part.strip() for part in parts]
        return [cast(part) for part in parts if part or not strip]
    resolved = _resolve_default(name, default=default, expected_type=list)
    if resolved is None:
        return None
    return list(resolved)

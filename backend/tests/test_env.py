from __future__ import annotations

from decimal import Decimal

import pytest
from src.utils.env import (
    ConfigurationError,
    env_bool,
    env_decimal,
    env_float,
    env_int,
    env_list,
    env_str,
)


def test_env_str_required(monkeypatch) -> None:
    monkeypatch.delenv("MISSING_STR", raising=False)
    with pytest.raises(ConfigurationError, match="MISSING_STR is required"):
        env_str("MISSING_STR")


def test_env_str_default_none(monkeypatch) -> None:
    monkeypatch.delenv("OPTIONAL_STR", raising=False)
    assert env_str("OPTIONAL_STR", default=None) is None


def test_env_str_default_value(monkeypatch) -> None:
    monkeypatch.delenv("OPTIONAL_STR", raising=False)
    assert env_str("OPTIONAL_STR", default="fallback") == "fallback"


def test_env_str_reads_value(monkeypatch) -> None:
    monkeypatch.setenv("MY_STR", "  hello  ")
    assert env_str("MY_STR") == "hello"


def test_env_str_blank_treated_as_unset(monkeypatch) -> None:
    monkeypatch.setenv("MY_STR", "   ")
    assert env_str("MY_STR", default=None) is None


def test_env_str_invalid_default_type() -> None:
    with pytest.raises(ConfigurationError, match="default must be str"):
        env_str("X", default=1)  # type: ignore[arg-type]


def test_env_bool_truthy_values(monkeypatch) -> None:
    for raw in ("true", "TRUE", "1", "yes", "on"):
        monkeypatch.setenv("FLAG", raw)
        assert env_bool("FLAG") is True


def test_env_bool_falsey_value(monkeypatch) -> None:
    monkeypatch.setenv("FLAG", "false")
    assert env_bool("FLAG") is False


def test_env_bool_default(monkeypatch) -> None:
    monkeypatch.delenv("FLAG", raising=False)
    assert env_bool("FLAG", default=True) is True


def test_env_int_conversion(monkeypatch) -> None:
    monkeypatch.setenv("COUNT", "42")
    assert env_int("COUNT") == 42


def test_env_int_invalid_raises(monkeypatch) -> None:
    monkeypatch.setenv("COUNT", "not-a-number")
    with pytest.raises(ConfigurationError, match="must be an integer"):
        env_int("COUNT")


def test_env_float_conversion(monkeypatch) -> None:
    monkeypatch.setenv("RATE", "3.14")
    assert env_float("RATE") == pytest.approx(3.14)


def test_env_decimal_conversion(monkeypatch) -> None:
    monkeypatch.setenv("AMOUNT", "19.99")
    assert env_decimal("AMOUNT") == Decimal("19.99")


def test_env_list_default(monkeypatch) -> None:
    monkeypatch.delenv("ORIGINS", raising=False)
    assert env_list("ORIGINS", default=["*"]) == ["*"]


def test_env_list_split_and_strip(monkeypatch) -> None:
    monkeypatch.setenv("ORIGINS", " https://a.com , https://b.com ")
    assert env_list("ORIGINS") == ["https://a.com", "https://b.com"]


def test_env_list_cast_int(monkeypatch) -> None:
    monkeypatch.setenv("PORTS", "1,2,3")
    assert env_list("PORTS", cast=int) == [1, 2, 3]


def test_env_list_custom_separator(monkeypatch) -> None:
    monkeypatch.setenv("TAGS", "a|b|c")
    assert env_list("TAGS", separator="|") == ["a", "b", "c"]

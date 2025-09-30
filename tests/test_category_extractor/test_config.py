"""Tests for configuration loading and validation."""
from __future__ import annotations

from typing import Iterable

import pytest

from src.ai_agents.category_extractor.config import (
    ExtractorConfig,
    get_config,
    reload_config,
)

_SENSITIVE_ENV_VARS: Iterable[str] = (
    "DB_PASSWORD",
    "AWS_ACCESS_KEY_ID",
    "AWS_SECRET_ACCESS_KEY",
    "DB_HOST",
    "DB_PORT",
    "DB_NAME",
    "DB_USER",
)


@pytest.fixture(autouse=True)
def reset_config(monkeypatch: pytest.MonkeyPatch) -> None:
    """Reset cached config and relevant env vars between tests."""
    for key in _SENSITIVE_ENV_VARS:
        monkeypatch.delenv(key, raising=False)
    reload_config()
    yield
    for key in _SENSITIVE_ENV_VARS:
        monkeypatch.delenv(key, raising=False)
    reload_config()


def test_get_config_returns_singleton(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("DB_PASSWORD", "testpass")
    monkeypatch.setenv("AWS_ACCESS_KEY_ID", "abc")
    monkeypatch.setenv("AWS_SECRET_ACCESS_KEY", "xyz")

    config_a = get_config()
    config_b = get_config()

    assert config_a is config_b


def test_reload_config_creates_new_instance(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("DB_PASSWORD", "pass1")
    monkeypatch.setenv("AWS_ACCESS_KEY_ID", "key1")
    monkeypatch.setenv("AWS_SECRET_ACCESS_KEY", "secret1")
    first = reload_config()

    monkeypatch.setenv("DB_PASSWORD", "pass2")
    monkeypatch.setenv("AWS_ACCESS_KEY_ID", "key2")
    monkeypatch.setenv("AWS_SECRET_ACCESS_KEY", "secret2")
    second = reload_config()

    assert first is not second
    assert second.db_password == "pass2"


def test_database_url_format(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("DB_HOST", "db-host")
    monkeypatch.setenv("DB_PORT", "6543")
    monkeypatch.setenv("DB_NAME", "prod")
    monkeypatch.setenv("DB_USER", "user")
    monkeypatch.setenv("DB_PASSWORD", "pwd")
    monkeypatch.setenv("AWS_ACCESS_KEY_ID", "key")
    monkeypatch.setenv("AWS_SECRET_ACCESS_KEY", "secret")

    config = reload_config()
    assert config.database_url == "postgresql://user:pwd@db-host:6543/prod"


def test_validate_config_requires_credentials(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("DB_PASSWORD", "pwd")

    config = reload_config()

    with pytest.raises(ValueError):
        config.validate_config()


def test_display_config_masks_sensitive_values(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("DB_PASSWORD", "pwd")
    monkeypatch.setenv("AWS_ACCESS_KEY_ID", "key")
    monkeypatch.setenv("AWS_SECRET_ACCESS_KEY", "secret")

    config = reload_config()
    displayed = config.display_config()

    assert displayed["db_password"] == "***MASKED***"
    assert displayed["aws_access_key_id"] == "***MASKED***"
    assert displayed["aws_secret_access_key"] == "***MASKED***"

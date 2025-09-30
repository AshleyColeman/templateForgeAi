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
    "OPENAI_API_KEY",
    "ANTHROPIC_API_KEY",
    "OPENROUTER_API_KEY",
    "DB_HOST",
    "DB_PORT",
    "DB_NAME",
    "DB_USER",
    "LLM_PROVIDER",
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
    monkeypatch.setenv("LLM_PROVIDER", "ollama")

    config_a = get_config()
    config_b = get_config()

    assert config_a is config_b


def test_reload_config_creates_new_instance(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("DB_PASSWORD", "pass1")
    monkeypatch.setenv("LLM_PROVIDER", "ollama")
    first = reload_config()

    monkeypatch.setenv("DB_PASSWORD", "pass2")
    monkeypatch.setenv("LLM_PROVIDER", "openai")
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test")
    second = reload_config()

    assert first is not second
    assert second.db_password == "pass2"
    assert second.llm_provider == "openai"


def test_database_url_format(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("DB_HOST", "db-host")
    monkeypatch.setenv("DB_PORT", "6543")
    monkeypatch.setenv("DB_NAME", "prod")
    monkeypatch.setenv("DB_USER", "user")
    monkeypatch.setenv("DB_PASSWORD", "pwd")
    monkeypatch.setenv("LLM_PROVIDER", "ollama")

    config = reload_config()
    assert config.database_url == "postgresql://user:pwd@db-host:6543/prod"


def test_validate_config_requires_credentials(tmp_path, monkeypatch: pytest.MonkeyPatch) -> None:
    # Test that OpenAI provider requires API key
    # Create a temporary .env file without API keys
    temp_env = tmp_path / ".env"
    temp_env.write_text("DB_PASSWORD=pwd\nLLM_PROVIDER=openai\n")
    
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.setattr("src.ai_agents.category_extractor.config._config", None)

    config = reload_config()

    with pytest.raises(ValueError, match="OPENAI_API_KEY"):
        config.validate_config()


def test_display_config_masks_sensitive_values(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("DB_PASSWORD", "pwd")
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test123")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-test456")
    monkeypatch.setenv("LLM_PROVIDER", "openai")

    config = reload_config()
    displayed = config.display_config()

    assert displayed["db_password"] == "***MASKED***"
    assert displayed["openai_api_key"] == "***MASKED***"
    assert displayed["anthropic_api_key"] == "***MASKED***"

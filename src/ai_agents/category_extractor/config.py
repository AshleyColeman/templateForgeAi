"""Configuration management using Pydantic settings."""
from __future__ import annotations

from typing import Dict, Optional

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class ExtractorConfig(BaseSettings):
    """Configuration for AI category extractor.

    All settings may be provided via environment variables or .env file.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Database configuration
    db_host: str = Field(default="localhost", description="PostgreSQL host")
    db_port: int = Field(default=5432, description="PostgreSQL port")
    db_name: str = Field(default="products", description="Database name")
    db_user: str = Field(default="postgres", description="Database user")
    db_password: str = Field(default="", description="Database password")

    @property
    def database_url(self) -> str:
        """Construct PostgreSQL DSN."""
        return (
            f"postgresql://{self.db_user}:{self.db_password}"
            f"@{self.db_host}:{self.db_port}/{self.db_name}"
        )

    # LLM Provider Configuration
    llm_provider: str = Field(
        default="ollama", 
        description="LLM provider: 'ollama', 'openai', 'anthropic', 'openrouter'"
    )
    
    # OpenAI Configuration
    openai_api_key: Optional[str] = Field(default=None, description="OpenAI API key")
    openai_model: str = Field(default="gpt-4o-mini", description="OpenAI model")
    openai_base_url: Optional[str] = Field(default=None, description="OpenAI base URL (for custom endpoints)")
    
    # Anthropic Configuration  
    anthropic_api_key: Optional[str] = Field(default=None, description="Anthropic API key")
    anthropic_model: str = Field(default="claude-3-5-sonnet-20241022", description="Anthropic model")
    
    # OpenRouter Configuration
    openrouter_api_key: Optional[str] = Field(default=None, description="OpenRouter API key")
    openrouter_model: str = Field(default="anthropic/claude-3.5-sonnet", description="OpenRouter model")
    
    # Ollama Configuration
    ollama_host: str = Field(default="http://localhost:11434", description="Ollama server host")
    ollama_model: str = Field(
        default="gemma3:1b",
        description="Ollama model (use gemma3:1b or deepseek-r1:1.5b for 8GB VRAM)",
    )
    ollama_keep_alive: str = Field(default="5m", description="How long model stays loaded")
    
    # Model (for backward compatibility)
    model_id: str = Field(
        default="gemma3:1b",
        description="Model identifier (defaults to provider-specific model)",
    )
    model_temperature: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="Model temperature (0.0-1.0)",
    )
    max_tokens: int = Field(
        default=4096,
        gt=0,
        le=200000,
        description="Maximum tokens per request",
    )

    # Browser
    browser_headless: bool = Field(default=True, description="Headless browser flag")
    browser_timeout: int = Field(default=60000, gt=0, description="Timeout in ms")
    browser_width: int = Field(default=1920, gt=0, description="Browser viewport width")
    browser_height: int = Field(default=1080, gt=0, description="Browser viewport height")

    # Extraction
    max_depth: int = Field(default=5, ge=0, le=10, description="Max category depth")
    max_categories: int = Field(default=10000, gt=0, description="Max categories to extract")
    max_retries: int = Field(default=3, ge=0, le=10, description="Retry attempts")
    retry_delay: int = Field(default=2000, gt=0, description="Retry delay in ms")

    # Blueprint
    blueprint_dir: str = Field(
        default="./src/ai_agents/category_extractor/blueprints",
        description="Directory for blueprints",
    )

    # Logging
    log_level: str = Field(default="INFO", description="Logging level")
    log_file: Optional[str] = Field(
        default="logs/category_extractor.log",
        description="Log file path",
    )
    log_rotation: str = Field(default="10 MB", description="Log file rotation size")
    log_retention: str = Field(default="30 days", description="Log retention policy")

    def validate_config(self) -> None:
        """Validate required secrets and enumerations."""
        if not self.db_password:
            raise ValueError("DB_PASSWORD must be set in environment")
        
        # Validate LLM provider configuration
        valid_providers = {"ollama", "openai", "anthropic", "openrouter"}
        if self.llm_provider not in valid_providers:
            raise ValueError(f"LLM_PROVIDER must be one of: {sorted(valid_providers)}")
        
        # Validate provider-specific credentials
        if self.llm_provider == "openai" and not self.openai_api_key:
            raise ValueError("OPENAI_API_KEY must be set when using OpenAI provider")
        elif self.llm_provider == "anthropic" and not self.anthropic_api_key:
            raise ValueError("ANTHROPIC_API_KEY must be set when using Anthropic provider")
        elif self.llm_provider == "openrouter" and not self.openrouter_api_key:
            raise ValueError("OPENROUTER_API_KEY must be set when using OpenRouter provider")
        # Ollama doesn't require API keys
        
        valid_levels = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
        if self.log_level.upper() not in valid_levels:
            raise ValueError(f"LOG_LEVEL must be one of: {sorted(valid_levels)}")

    def display_config(self) -> Dict[str, Optional[str]]:
        """Return config for display with sensitive values masked."""
        data: Dict[str, Optional[str]] = self.model_dump()
        sensitive_keys = (
            "db_password", "openai_api_key", "anthropic_api_key", "openrouter_api_key"
        )
        for key in sensitive_keys:
            if data.get(key):
                data[key] = "***MASKED***"
        return data


_config: Optional[ExtractorConfig] = None


def get_config() -> ExtractorConfig:
    """Return singleton configuration instance."""
    global _config
    if _config is None:
        _config = ExtractorConfig()
    return _config


def reload_config() -> ExtractorConfig:
    """Reload configuration from environment (useful in tests)."""
    global _config
    _config = ExtractorConfig()
    return _config


__all__ = ["ExtractorConfig", "get_config", "reload_config"]

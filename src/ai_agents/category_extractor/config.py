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

    # AWS
    aws_region: str = Field(default="us-east-1", description="AWS region")
    aws_access_key_id: Optional[str] = Field(default=None, description="AWS access key")
    aws_secret_access_key: Optional[str] = Field(default=None, description="AWS secret key")

    # Model
    model_id: str = Field(
        default="us.anthropic.claude-sonnet-4-20250514-v1:0",
        description="AWS Bedrock model identifier",
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
        if not self.aws_access_key_id or not self.aws_secret_access_key:
            raise ValueError("AWS credentials must be set in environment")
        valid_levels = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
        if self.log_level.upper() not in valid_levels:
            raise ValueError(f"LOG_LEVEL must be one of: {sorted(valid_levels)}")

    def display_config(self) -> Dict[str, Optional[str]]:
        """Return config for display with sensitive values masked."""
        data: Dict[str, Optional[str]] = self.model_dump()
        for key in ("db_password", "aws_access_key_id", "aws_secret_access_key"):
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

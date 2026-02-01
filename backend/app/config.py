"""Application configuration using Pydantic Settings."""

from functools import lru_cache
from typing import Literal

from pydantic import Field, RedisDsn, computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Environment
    environment: Literal["development", "testing", "production"] = "development"
    debug: bool = Field(default=False)
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = "INFO"

    # Database
    postgres_user: str = "gha"
    postgres_password: str = "gha_secret"
    postgres_host: str = "localhost"
    postgres_port: int = 5432
    postgres_db: str = "github_actions"

    @computed_field  # type: ignore[prop-decorator]
    @property
    def database_url(self) -> str:
        """Construct async database URL."""
        return (
            f"postgresql+asyncpg://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )

    @computed_field  # type: ignore[prop-decorator]
    @property
    def database_url_sync(self) -> str:
        """Construct sync database URL for Alembic."""
        return (
            f"postgresql://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )

    # Redis
    redis_url: RedisDsn = Field(default="redis://localhost:6379/0")  # type: ignore[assignment]

    # GitHub
    github_token: str = Field(default="")
    github_webhook_secret: str = Field(default="")
    github_org: str = Field(default="")
    github_api_base_url: str = "https://api.github.com"

    # LLM APIs
    anthropic_api_key: str = Field(default="")
    openai_api_key: str = Field(default="")

    # Claude settings
    claude_model: str = "claude-sonnet-4-20250514"
    claude_max_tokens: int = 4096

    # OpenAI settings
    openai_embedding_model: str = "text-embedding-3-small"
    openai_embedding_dimensions: int = 1536

    # Application
    secret_key: str = Field(default="change-me-in-production")
    api_v1_prefix: str = "/api/v1"

    # Data retention
    data_retention_days: int = 30

    # Rate limiting
    rate_limit_requests: int = 100
    rate_limit_period: int = 60  # seconds

    # Notifications
    slack_webhook_url: str = Field(default="")
    discord_webhook_url: str = Field(default="")

    # Self-monitoring
    self_monitoring_enabled: bool = Field(default=False)
    self_monitoring_repo: str = Field(default="")


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()

"""Application configuration using Pydantic Settings."""

from functools import lru_cache
from typing import Literal
from urllib.parse import quote_plus

from pydantic import Field, RedisDsn, computed_field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# Known-weak default values that must never be used in production.
# Centralised so verify_api_key, websocket auth, and the production
# validator all agree on what counts as "unset".
WEAK_SECRET_KEY_VALUES: frozenset[str] = frozenset({"", "change-me-in-production"})
WEAK_POSTGRES_PASSWORDS: frozenset[str] = frozenset({"", "gha_secret", "postgres"})
WEAK_REDIS_PASSWORDS: frozenset[str] = frozenset({"", "redis_secret"})


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
        """Construct async database URL (password is URL-encoded)."""
        password = quote_plus(self.postgres_password)
        return (
            f"postgresql+asyncpg://{self.postgres_user}:{password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )

    @computed_field  # type: ignore[prop-decorator]
    @property
    def database_url_sync(self) -> str:
        """Construct sync database URL for Alembic (password is URL-encoded)."""
        password = quote_plus(self.postgres_password)
        return (
            f"postgresql://{self.postgres_user}:{password}"
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

    # CORS — comma-separated allowed origins (e.g. "https://app.example.com")
    cors_origins: list[str] = Field(default=["http://localhost:3000", "http://localhost:5173"])

    # Trusted hosts (production) — leave empty to disable
    trusted_hosts: list[str] = Field(default_factory=list)

    # Maximum WebSocket connections
    max_ws_connections: int = Field(default=100)

    # Self-monitoring
    self_monitoring_enabled: bool = Field(default=False)
    self_monitoring_repo: str = Field(default="")

    @model_validator(mode="after")
    def _enforce_production_secrets(self) -> "Settings":
        """Refuse to start in production with weak/unset secrets or insecure CORS."""
        if self.environment != "production":
            return self

        errors: list[str] = []

        if self.secret_key in WEAK_SECRET_KEY_VALUES:
            errors.append(
                "SECRET_KEY must be set to a strong, random value in production "
                "(current value is empty or a known default)."
            )
        if self.postgres_password in WEAK_POSTGRES_PASSWORDS:
            errors.append(
                "POSTGRES_PASSWORD must be set to a strong, non-default value in production."
            )
        redis_url_str = str(self.redis_url)
        for weak in WEAK_REDIS_PASSWORDS:
            # Skip the empty-string marker since every URL technically "contains" ""
            if weak and f":{weak}@" in redis_url_str:
                errors.append(
                    "REDIS_URL must not embed the known-default password "
                    f"'{weak}' in production."
                )
                break

        for origin in self.cors_origins:
            if origin.startswith("http://") and "localhost" not in origin:
                errors.append(
                    f"CORS origin '{origin}' uses http:// in production. "
                    "All non-localhost origins must use https://."
                )

        if errors:
            raise ValueError(
                "Insecure production configuration:\n  - " + "\n  - ".join(errors)
            )

        return self


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()

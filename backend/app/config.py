"""Application configuration using Pydantic Settings."""

import secrets
from functools import lru_cache
from typing import Literal

from pydantic import (
    Field,
    RedisDsn,
    ValidationInfo,
    computed_field,
    field_validator,
    model_validator,
)
from pydantic_settings import BaseSettings, SettingsConfigDict


class APIKeyConfig(BaseSettings):
    """API key configuration."""

    model_config = SettingsConfigDict(extra="ignore")

    id: str
    name: str
    key_hash: str
    scopes: list[str] = Field(default_factory=list)


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

    # Database - no hardcoded defaults for credentials
    postgres_user: str = Field(default="")
    postgres_password: str = Field(default="")
    postgres_host: str = Field(default="localhost")
    postgres_port: int = Field(default=5432)
    postgres_db: str = Field(default="github_actions")
    postgres_ssl_mode: Literal["disable", "require", "verify-ca", "verify-full"] = Field(
        default="disable"
    )

    @computed_field  # type: ignore[prop-decorator]
    @property
    def database_url(self) -> str:
        """Construct async database URL."""
        base_url = (
            f"postgresql+asyncpg://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )
        if self.postgres_ssl_mode != "disable":
            return f"{base_url}?ssl={self.postgres_ssl_mode}"
        return base_url

    @computed_field  # type: ignore[prop-decorator]
    @property
    def database_url_sync(self) -> str:
        """Construct sync database URL for Alembic."""
        base_url = (
            f"postgresql://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )
        if self.postgres_ssl_mode != "disable":
            return f"{base_url}?sslmode={self.postgres_ssl_mode}"
        return base_url

    # Redis - support authentication
    redis_url: RedisDsn = Field(default="redis://localhost:6379/0")  # type: ignore[assignment]
    redis_password: str = Field(default="")

    @computed_field  # type: ignore[prop-decorator]
    @property
    def redis_url_with_auth(self) -> str:
        """Construct Redis URL with authentication if password is set."""
        base_url = str(self.redis_url)
        if self.redis_password and "://" in base_url:
            # Insert password into URL
            scheme, rest = base_url.split("://", 1)
            return f"{scheme}//:{self.redis_password}@{rest}"
        return base_url

    # GitHub
    github_token: str = Field(default="")
    github_webhook_secret: str = Field(default="")
    github_org: str = Field(default="")
    github_api_base_url: str = Field(default="https://api.github.com")

    # LLM APIs
    anthropic_api_key: str = Field(default="")
    openai_api_key: str = Field(default="")

    # Claude settings
    claude_model: str = Field(default="claude-sonnet-4-20250514")
    claude_max_tokens: int = Field(default=4096)

    # OpenAI settings
    openai_embedding_model: str = Field(default="text-embedding-3-small")
    openai_embedding_dimensions: int = Field(default=1536)

    # Application Security
    secret_key: str = Field(default="")
    api_v1_prefix: str = Field(default="/api/v1")

    # Authentication - set to True to require authentication on all endpoints
    require_authentication: bool = Field(default=False)

    # CORS configuration
    cors_origins: list[str] = Field(default_factory=lambda: ["http://localhost:3000", "http://localhost:5173"])
    cors_allow_credentials: bool = Field(default=True)
    cors_allow_methods: list[str] = Field(default_factory=lambda: ["GET", "POST", "PUT", "DELETE", "OPTIONS"])
    cors_allow_headers: list[str] = Field(default_factory=lambda: ["Authorization", "Content-Type", "X-Requested-With"])

    # Allowed hosts (for host header validation)
    allowed_hosts: list[str] = Field(default_factory=lambda: ["localhost", "127.0.0.1"])

    # Data retention
    data_retention_days: int = Field(default=30)

    # Rate limiting
    rate_limit_enabled: bool = Field(default=True)
    rate_limit_requests: int = Field(default=100)
    rate_limit_period: int = Field(default=60)  # seconds
    webhook_rate_limit_requests: int = Field(default=30)
    webhook_rate_limit_period: int = Field(default=60)

    # Request size limits
    max_request_size_mb: int = Field(default=10)

    # Notifications
    slack_webhook_url: str = Field(default="")
    discord_webhook_url: str = Field(default="")

    # Self-monitoring
    self_monitoring_enabled: bool = Field(default=False)
    self_monitoring_repo: str = Field(default="")

    # API Keys (for programmatic access)
    api_keys: list[APIKeyConfig] = Field(default_factory=list)

    @field_validator("secret_key")
    @classmethod
    def validate_secret_key(cls, v: str, info: ValidationInfo) -> str:
        """Validate secret key is set in non-development environments."""
        # Get environment from the data being validated
        env = info.data.get("environment", "development") if info.data else "development"

        # In development/testing, generate a random key if not set
        if not v or v == "change-me-in-production":
            if env == "production":
                raise ValueError(
                    "SECRET_KEY must be set to a secure value in production. "
                    "Generate one with: python -c \"import secrets; print(secrets.token_urlsafe(32))\""
                )
            # Generate a random key for development/testing
            return secrets.token_urlsafe(32)
        return v

    @field_validator("github_webhook_secret")
    @classmethod
    def validate_webhook_secret(cls, v: str, info: ValidationInfo) -> str:
        """Warn if webhook secret is not set."""
        env = info.data.get("environment", "development") if info.data else "development"
        if not v and env == "production":
            import logging
            logging.warning(
                "GITHUB_WEBHOOK_SECRET is not set. Webhook signature validation will be skipped. "
                "This is a security risk in production."
            )
        return v

    @model_validator(mode="after")
    def validate_production_settings(self) -> "Settings":
        """Validate all required settings for production."""
        if self.environment == "production":
            errors = []

            if not self.postgres_user:
                errors.append("POSTGRES_USER must be set in production")
            if not self.postgres_password:
                errors.append("POSTGRES_PASSWORD must be set in production")
            if self.debug:
                errors.append("DEBUG must be False in production")

            if errors:
                raise ValueError(f"Production validation failed: {'; '.join(errors)}")

        return self


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()

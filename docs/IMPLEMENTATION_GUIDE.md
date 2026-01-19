# GitHub Actions Dashboard - Implementation Guide

## Purpose
This guide provides step-by-step instructions for Claude CLI to implement the GitHub Actions Dashboard. Execute these steps in order.

---

## Step 1: Initialize Project Structure

### 1.1 Create Directory Structure
```bash
mkdir -p github-actions-dashboard/{backend,frontend,docker,docs,scripts,.github/workflows,monitoring}
cd github-actions-dashboard
git init
```

### 1.2 Initialize Backend with UV
```bash
cd backend

# Initialize UV project
uv init --name github-actions-dashboard --python 3.12

# Add dependencies
uv add \
  fastapi==0.115.6 \
  uvicorn[standard]==0.34.0 \
  pydantic==2.10.4 \
  pydantic-settings==2.7.0 \
  sqlalchemy==2.0.36 \
  alembic==1.14.0 \
  asyncpg==0.30.0 \
  pgvector==0.3.6 \
  redis==5.2.1 \
  celery==5.4.0 \
  httpx==0.28.1 \
  anthropic==0.40.0 \
  openai==1.58.1 \
  prometheus-client==0.21.1 \
  python-json-logger==2.0.7 \
  sentry-sdk[fastapi]==2.19.2

# Add dev dependencies
uv add --dev \
  pytest==8.3.4 \
  pytest-asyncio==0.25.0 \
  pytest-cov==6.0.0 \
  pytest-xdist==3.5.0 \
  pytest-mock==3.14.0 \
  factory-boy==3.3.1 \
  faker==33.1.0 \
  respx==0.22.0 \
  hypothesis==6.122.3 \
  testcontainers==4.8.2 \
  freezegun==1.4.0 \
  ruff==0.8.4 \
  mypy==1.14.1 \
  bandit==1.8.0 \
  pre-commit==4.0.1
```

### 1.3 Create Backend Structure
```bash
mkdir -p app/{api/v1,domain/{entities,value_objects,events,repositories},application/{services,commands,queries},infrastructure/{database/{models,repositories},external,cache},tasks,core,schemas}
mkdir -p tests/{unit/{application/services,api},integration,property,e2e,fixtures/{log_samples,github_responses}}
mkdir -p migrations/versions

touch app/__init__.py
touch app/api/__init__.py
touch app/api/v1/__init__.py
touch app/domain/__init__.py
touch app/domain/entities/__init__.py
touch app/domain/value_objects/__init__.py
touch app/domain/events/__init__.py
touch app/domain/repositories/__init__.py
touch app/application/__init__.py
touch app/application/services/__init__.py
touch app/application/commands/__init__.py
touch app/application/queries/__init__.py
touch app/infrastructure/__init__.py
touch app/infrastructure/database/__init__.py
touch app/infrastructure/database/models/__init__.py
touch app/infrastructure/database/repositories/__init__.py
touch app/infrastructure/external/__init__.py
touch app/infrastructure/cache/__init__.py
touch app/tasks/__init__.py
touch app/core/__init__.py
touch app/schemas/__init__.py
touch tests/__init__.py
```

---

## Step 2: Implement Configuration

### 2.1 Create config.py
Create `backend/app/config.py`:

```python
"""Application configuration using Pydantic Settings."""
from functools import lru_cache
from typing import Literal

from pydantic import Field, PostgresDsn, RedisDsn, computed_field
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
    
    @computed_field
    @property
    def database_url(self) -> str:
        """Construct async database URL."""
        return f"postgresql+asyncpg://{self.postgres_user}:{self.postgres_password}@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
    
    @computed_field
    @property
    def database_url_sync(self) -> str:
        """Construct sync database URL for Alembic."""
        return f"postgresql://{self.postgres_user}:{self.postgres_password}@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
    
    # Redis
    redis_url: RedisDsn = Field(default="redis://localhost:6379/0")
    
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


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
```

### 2.2 Create main.py
Create `backend/app/main.py`:

```python
"""FastAPI application entry point."""
import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import get_settings
from app.core.exceptions import AppException
from app.core.logging import setup_logging

settings = get_settings()
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan handler."""
    setup_logging(settings.log_level)
    logger.info(
        "Starting GitHub Actions Dashboard",
        extra={"environment": settings.environment},
    )
    yield
    logger.info("Shutting down GitHub Actions Dashboard")


def create_app() -> FastAPI:
    """Create and configure FastAPI application."""
    app = FastAPI(
        title="GitHub Actions Dashboard",
        description="Monitor and analyze GitHub Actions workflows with LLM integration",
        version="0.1.0",
        docs_url="/docs" if settings.environment != "production" else None,
        redoc_url="/redoc" if settings.environment != "production" else None,
        lifespan=lifespan,
    )
    
    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:3000", "http://localhost:5173"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Exception handlers
    @app.exception_handler(AppException)
    async def app_exception_handler(request: Request, exc: AppException) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status_code,
            content={"detail": exc.message, "code": exc.code},
        )
    
    @app.exception_handler(Exception)
    async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        logger.exception("Unhandled exception")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"detail": "Internal server error"},
        )
    
    # Health endpoints
    @app.get("/health", tags=["Health"])
    async def health_check() -> dict[str, str]:
        """Basic health check."""
        return {"status": "healthy"}
    
    @app.get("/health/ready", tags=["Health"])
    async def readiness_check() -> dict[str, str | dict[str, bool]]:
        """Readiness check with dependency status."""
        # TODO: Add actual dependency checks
        return {
            "status": "ready",
            "checks": {
                "database": True,
                "redis": True,
            },
        }
    
    @app.get("/health/live", tags=["Health"])
    async def liveness_check() -> dict[str, str]:
        """Liveness probe."""
        return {"status": "alive"}
    
    # Include routers
    # from app.api.v1.router import api_router
    # app.include_router(api_router, prefix=settings.api_v1_prefix)
    
    return app


app = create_app()
```

### 2.3 Create Core Modules
Create `backend/app/core/exceptions.py`:

```python
"""Custom application exceptions."""
from typing import Any


class AppException(Exception):
    """Base application exception."""
    
    def __init__(
        self,
        message: str,
        code: str = "APP_ERROR",
        status_code: int = 500,
        details: dict[str, Any] | None = None,
    ) -> None:
        self.message = message
        self.code = code
        self.status_code = status_code
        self.details = details or {}
        super().__init__(message)


class NotFoundError(AppException):
    """Resource not found."""
    
    def __init__(self, resource: str, identifier: Any) -> None:
        super().__init__(
            message=f"{resource} with id {identifier} not found",
            code="NOT_FOUND",
            status_code=404,
        )


class ValidationError(AppException):
    """Validation error."""
    
    def __init__(self, message: str, details: dict[str, Any] | None = None) -> None:
        super().__init__(
            message=message,
            code="VALIDATION_ERROR",
            status_code=422,
            details=details,
        )


class GitHubAPIError(AppException):
    """GitHub API error."""
    
    def __init__(self, message: str, status_code: int = 502) -> None:
        super().__init__(
            message=message,
            code="GITHUB_API_ERROR",
            status_code=status_code,
        )


class LLMError(AppException):
    """LLM API error."""
    
    def __init__(self, message: str, provider: str = "unknown") -> None:
        super().__init__(
            message=message,
            code="LLM_ERROR",
            status_code=502,
            details={"provider": provider},
        )


class WebhookValidationError(AppException):
    """Webhook validation failed."""
    
    def __init__(self, message: str = "Invalid webhook signature") -> None:
        super().__init__(
            message=message,
            code="WEBHOOK_VALIDATION_ERROR",
            status_code=401,
        )
```

Create `backend/app/core/logging.py`:

```python
"""Logging configuration."""
import logging
import sys
from typing import Literal

from pythonjsonlogger import jsonlogger


def setup_logging(level: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = "INFO") -> None:
    """Configure structured JSON logging."""
    logger = logging.getLogger()
    logger.setLevel(level)
    
    # Remove existing handlers
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)
    
    # JSON handler for stdout
    handler = logging.StreamHandler(sys.stdout)
    formatter = jsonlogger.JsonFormatter(
        "%(asctime)s %(levelname)s %(name)s %(message)s",
        rename_fields={"asctime": "timestamp", "levelname": "level"},
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    
    # Suppress noisy loggers
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
```

---

## Step 3: Implement Database Models

### 3.1 Create Base Model
Create `backend/app/infrastructure/database/models/base.py`:

```python
"""SQLAlchemy base model and common utilities."""
from datetime import datetime
from typing import Any

from sqlalchemy import MetaData, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

# Naming convention for constraints
convention = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}


class Base(DeclarativeBase):
    """Base class for all models."""
    
    metadata = MetaData(naming_convention=convention)
    
    def to_dict(self) -> dict[str, Any]:
        """Convert model to dictionary."""
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}


class TimestampMixin:
    """Mixin for created_at and updated_at timestamps."""
    
    created_at: Mapped[datetime] = mapped_column(
        default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
```

### 3.2 Create All Models
Create `backend/app/infrastructure/database/models/repository.py`:

```python
"""Repository model."""
from datetime import datetime

from sqlalchemy import BigInteger, Boolean, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.infrastructure.database.models.base import Base, TimestampMixin


class Repository(Base, TimestampMixin):
    """GitHub repository being monitored."""
    
    __tablename__ = "repositories"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    github_id: Mapped[int] = mapped_column(BigInteger, unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    owner: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, index=True)
    webhook_configured: Mapped[bool] = mapped_column(Boolean, default=False)
    last_synced_at: Mapped[datetime | None] = mapped_column()
    
    # Relationships
    workflows: Mapped[list["Workflow"]] = relationship(
        back_populates="repository",
        cascade="all, delete-orphan",
    )
```

Create additional models for: Workflow, WorkflowRun, Job, JobStep, Log, TestResult, ErrorAnalysis, Artifact.

(Continue with similar patterns for all models defined in the schema)

### 3.3 Create Database Session
Create `backend/app/infrastructure/database/session.py`:

```python
"""Database session management."""
from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.config import get_settings

settings = get_settings()

engine = create_async_engine(
    settings.database_url,
    echo=settings.debug,
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20,
)

AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Dependency for database session."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
```

---

## Step 4: Implement Application Services

### 4.1 Test Result Parser
Create `backend/app/application/services/test_result_parser.py`:

```python
"""Multi-framework test result parser."""
from __future__ import annotations

import re
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Protocol


@dataclass(frozen=True)
class FailureDetail:
    """Details of a single test failure."""
    
    test_name: str
    error_message: str
    stack_trace: str | None = None
    file_path: str | None = None
    line_number: int | None = None


@dataclass(frozen=True)
class TestResult:
    """Immutable test result value object."""
    
    framework: str
    total: int
    passed: int
    failed: int
    skipped: int
    duration_seconds: float | None = None
    failures: list[FailureDetail] = field(default_factory=list)
    
    @property
    def success_rate(self) -> float:
        """Calculate success rate as percentage."""
        if self.total == 0:
            return 0.0
        return (self.passed / self.total) * 100


class TestResultParser(Protocol):
    """Protocol for test result parsers."""
    
    def can_parse(self, log_content: str) -> bool:
        """Check if this parser can handle the log content."""
        ...
    
    def parse(self, log_content: str) -> TestResult | None:
        """Parse log content and extract test results."""
        ...


class BaseParser(ABC):
    """Base class for parsers with common utilities."""
    
    @staticmethod
    def strip_ansi(text: str) -> str:
        """Remove ANSI color codes from text."""
        ansi_pattern = re.compile(r'\x1b\[[0-9;]*m')
        return ansi_pattern.sub('', text)
    
    @staticmethod
    def strip_docker_noise(text: str) -> str:
        """Remove Docker container prefixes and timestamps."""
        lines = text.split('\n')
        cleaned_lines = []
        for line in lines:
            # Remove Docker timestamp prefixes like "2024-01-15T10:00:00.000Z "
            line = re.sub(r'^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}[.\d]*Z?\s*', '', line)
            # Remove container name prefixes like "[container-name] "
            line = re.sub(r'^\[[\w-]+\]\s*', '', line)
            cleaned_lines.append(line)
        return '\n'.join(cleaned_lines)
    
    def preprocess(self, log_content: str) -> str:
        """Preprocess log content before parsing."""
        content = self.strip_ansi(log_content)
        content = self.strip_docker_noise(content)
        return content
    
    @abstractmethod
    def can_parse(self, log_content: str) -> bool:
        """Check if this parser can handle the log content."""
        ...
    
    @abstractmethod
    def parse(self, log_content: str) -> TestResult | None:
        """Parse log content and extract test results."""
        ...


class PytestParser(BaseParser):
    """Parser for pytest output."""
    
    # Patterns for pytest output
    SUMMARY_PATTERN = re.compile(
        r'[=]+ (?:(?P<passed>\d+) passed)?'
        r'(?:, )?(?:(?P<failed>\d+) failed)?'
        r'(?:, )?(?:(?P<error>\d+) error)?'
        r'(?:, )?(?:(?P<skipped>\d+) skipped)?'
        r'(?:, )?(?:(?P<xfailed>\d+) xfailed)?'
        r'(?:, )?(?:(?P<xpassed>\d+) xpassed)?'
        r'(?: in (?P<duration>[\d.]+)s)?'
    )
    COLLECTED_PATTERN = re.compile(r'collected (\d+) items?')
    FAILURE_PATTERN = re.compile(
        r'_{5,} (?P<test_name>[\w\[\]._-]+) _{5,}',
        re.MULTILINE
    )
    
    def can_parse(self, log_content: str) -> bool:
        """Check for pytest indicators."""
        content = self.preprocess(log_content)
        indicators = [
            'collected',
            'pytest',
            '===',
            'PASSED',
            'FAILED',
            'ERROR',
        ]
        return any(ind in content for ind in indicators) and self.SUMMARY_PATTERN.search(content) is not None
    
    def parse(self, log_content: str) -> TestResult | None:
        """Parse pytest output."""
        content = self.preprocess(log_content)
        
        # Find summary line
        match = self.SUMMARY_PATTERN.search(content)
        if not match:
            return None
        
        groups = match.groupdict()
        passed = int(groups.get('passed') or 0)
        failed = int(groups.get('failed') or 0) + int(groups.get('error') or 0)
        skipped = int(groups.get('skipped') or 0) + int(groups.get('xfailed') or 0)
        duration = float(groups['duration']) if groups.get('duration') else None
        
        # Extract total from collected
        collected_match = self.COLLECTED_PATTERN.search(content)
        total = int(collected_match.group(1)) if collected_match else passed + failed + skipped
        
        # Extract failure details
        failures = self._extract_failures(content)
        
        return TestResult(
            framework="pytest",
            total=total,
            passed=passed,
            failed=failed,
            skipped=skipped,
            duration_seconds=duration,
            failures=failures,
        )
    
    def _extract_failures(self, content: str) -> list[FailureDetail]:
        """Extract failure details from pytest output."""
        failures = []
        for match in self.FAILURE_PATTERN.finditer(content):
            test_name = match.group('test_name')
            # Find the error message after this header
            start = match.end()
            next_match = self.FAILURE_PATTERN.search(content, start)
            end = next_match.start() if next_match else len(content)
            error_block = content[start:end]
            
            # Extract error message (first line after "E ")
            error_lines = [
                line[2:] for line in error_block.split('\n')
                if line.startswith('E ')
            ]
            error_message = '\n'.join(error_lines) if error_lines else "Unknown error"
            
            failures.append(FailureDetail(
                test_name=test_name,
                error_message=error_message[:500],  # Truncate
                stack_trace=error_block[:2000] if len(error_block) > 0 else None,
            ))
        
        return failures


class JestParser(BaseParser):
    """Parser for Jest output."""
    
    SUMMARY_PATTERN = re.compile(
        r'Tests:\s+(?:(?P<failed>\d+) failed,?\s*)?'
        r'(?:(?P<skipped>\d+) skipped,?\s*)?'
        r'(?:(?P<passed>\d+) passed,?\s*)?'
        r'(?P<total>\d+) total'
    )
    TIME_PATTERN = re.compile(r'Time:\s+([\d.]+)\s*s')
    
    def can_parse(self, log_content: str) -> bool:
        """Check for Jest indicators."""
        content = self.preprocess(log_content)
        return 'Tests:' in content and ('passed' in content or 'failed' in content)
    
    def parse(self, log_content: str) -> TestResult | None:
        """Parse Jest output."""
        content = self.preprocess(log_content)
        
        match = self.SUMMARY_PATTERN.search(content)
        if not match:
            return None
        
        groups = match.groupdict()
        time_match = self.TIME_PATTERN.search(content)
        
        return TestResult(
            framework="jest",
            total=int(groups.get('total') or 0),
            passed=int(groups.get('passed') or 0),
            failed=int(groups.get('failed') or 0),
            skipped=int(groups.get('skipped') or 0),
            duration_seconds=float(time_match.group(1)) if time_match else None,
        )


class GoTestParser(BaseParser):
    """Parser for Go test output."""
    
    PASS_PATTERN = re.compile(r'^--- PASS:', re.MULTILINE)
    FAIL_PATTERN = re.compile(r'^--- FAIL:', re.MULTILINE)
    SKIP_PATTERN = re.compile(r'^--- SKIP:', re.MULTILINE)
    RESULT_PATTERN = re.compile(r'^(ok|FAIL)\s+\S+\s+([\d.]+)s', re.MULTILINE)
    
    def can_parse(self, log_content: str) -> bool:
        """Check for Go test indicators."""
        content = self.preprocess(log_content)
        return ('--- PASS:' in content or '--- FAIL:' in content or 
                content.startswith('ok ') or 'FAIL\t' in content)
    
    def parse(self, log_content: str) -> TestResult | None:
        """Parse Go test output."""
        content = self.preprocess(log_content)
        
        passed = len(self.PASS_PATTERN.findall(content))
        failed = len(self.FAIL_PATTERN.findall(content))
        skipped = len(self.SKIP_PATTERN.findall(content))
        
        # Get duration from result line
        duration = None
        for match in self.RESULT_PATTERN.finditer(content):
            duration = float(match.group(2))
        
        return TestResult(
            framework="go-test",
            total=passed + failed + skipped,
            passed=passed,
            failed=failed,
            skipped=skipped,
            duration_seconds=duration,
        )


# Add more parsers: RSpecParser, MochaParser, VitestParser, etc.
# Follow the same pattern


class TestResultParserService:
    """Service that orchestrates multiple test result parsers."""
    
    def __init__(self, parsers: list[TestResultParser] | None = None) -> None:
        """Initialize with parsers, using defaults if none provided."""
        self._parsers = parsers or self._get_default_parsers()
    
    @staticmethod
    def _get_default_parsers() -> list[TestResultParser]:
        """Get default list of parsers."""
        return [
            PytestParser(),
            JestParser(),
            GoTestParser(),
            # Add other parsers
        ]
    
    def parse(self, log_content: str) -> TestResult | None:
        """Try all parsers until one succeeds."""
        for parser in self._parsers:
            if parser.can_parse(log_content):
                result = parser.parse(log_content)
                if result is not None:
                    return result
        return None
```

### 4.2 Webhook Processor
Create `backend/app/application/services/webhook_processor.py`:

```python
"""Webhook processing service."""
from __future__ import annotations

import hashlib
import hmac
import logging
from dataclasses import dataclass
from typing import Protocol

from app.config import get_settings
from app.core.exceptions import WebhookValidationError

logger = logging.getLogger(__name__)
settings = get_settings()


@dataclass(frozen=True)
class WebhookEvent:
    """Validated webhook event."""
    
    event_type: str
    action: str
    delivery_id: str
    payload: dict


class WebhookValidator(Protocol):
    """Protocol for webhook signature validation."""
    
    def validate(self, payload: bytes, signature: str) -> bool:
        """Validate webhook signature."""
        ...


class GitHubWebhookValidator:
    """GitHub-specific webhook validation."""
    
    def __init__(self, secret: str) -> None:
        """Initialize with webhook secret."""
        self._secret = secret.encode()
    
    def validate(self, payload: bytes, signature: str) -> bool:
        """Validate GitHub webhook signature."""
        if not signature.startswith("sha256="):
            return False
        
        expected = hmac.new(
            self._secret,
            payload,
            hashlib.sha256,
        ).hexdigest()
        
        return hmac.compare_digest(f"sha256={expected}", signature)


class IdempotencyStore(Protocol):
    """Protocol for idempotency tracking."""
    
    async def exists(self, delivery_id: str) -> bool:
        """Check if delivery has been processed."""
        ...
    
    async def mark_processed(self, delivery_id: str) -> None:
        """Mark delivery as processed."""
        ...


@dataclass
class ProcessResult:
    """Result of webhook processing."""
    
    status: str  # "queued", "duplicate", "error"
    delivery_id: str
    message: str | None = None


class WebhookProcessor:
    """Process incoming webhooks with idempotency."""
    
    def __init__(
        self,
        validator: WebhookValidator,
        idempotency_store: IdempotencyStore,
    ) -> None:
        """Initialize webhook processor."""
        self._validator = validator
        self._idempotency = idempotency_store
    
    async def process(
        self,
        payload: bytes,
        signature: str,
        event_type: str,
        delivery_id: str,
    ) -> ProcessResult:
        """Process webhook with validation and idempotency."""
        # Validate signature
        if not self._validator.validate(payload, signature):
            logger.warning(
                "Invalid webhook signature",
                extra={"delivery_id": delivery_id},
            )
            raise WebhookValidationError()
        
        # Check idempotency
        if await self._idempotency.exists(delivery_id):
            logger.info(
                "Duplicate webhook received",
                extra={"delivery_id": delivery_id},
            )
            return ProcessResult(
                status="duplicate",
                delivery_id=delivery_id,
                message="Webhook already processed",
            )
        
        # Mark as processed
        await self._idempotency.mark_processed(delivery_id)
        
        logger.info(
            "Webhook queued for processing",
            extra={
                "delivery_id": delivery_id,
                "event_type": event_type,
            },
        )
        
        return ProcessResult(
            status="queued",
            delivery_id=delivery_id,
        )
```

---

## Step 5: Create API Endpoints

### 5.1 Create API Router
Create `backend/app/api/v1/router.py`:

```python
"""API v1 router aggregator."""
from fastapi import APIRouter

from app.api.v1 import health, webhooks, workflows, runs, jobs, analysis, search

api_router = APIRouter()

api_router.include_router(health.router, tags=["Health"])
api_router.include_router(webhooks.router, prefix="/webhooks", tags=["Webhooks"])
api_router.include_router(workflows.router, prefix="/workflows", tags=["Workflows"])
api_router.include_router(runs.router, prefix="/runs", tags=["Runs"])
api_router.include_router(jobs.router, prefix="/jobs", tags=["Jobs"])
api_router.include_router(analysis.router, prefix="/analysis", tags=["Analysis"])
api_router.include_router(search.router, prefix="/search", tags=["Search"])
```

### 5.2 Create Webhook Endpoint
Create `backend/app/api/v1/webhooks.py`:

```python
"""GitHub webhook endpoints."""
import json
import logging
from typing import Annotated

from fastapi import APIRouter, Header, Request, status
from fastapi.responses import JSONResponse

from app.application.services.webhook_processor import (
    GitHubWebhookValidator,
    WebhookProcessor,
)
from app.config import get_settings
from app.core.exceptions import WebhookValidationError

logger = logging.getLogger(__name__)
router = APIRouter()
settings = get_settings()


@router.post("/github")
async def github_webhook(
    request: Request,
    x_github_event: Annotated[str, Header()],
    x_hub_signature_256: Annotated[str, Header()],
    x_github_delivery: Annotated[str, Header()],
) -> JSONResponse:
    """
    Handle GitHub webhook events.
    
    Processes workflow_run and workflow_job events.
    Returns 202 Accepted and queues for async processing.
    """
    payload = await request.body()
    
    # Create validator and processor
    validator = GitHubWebhookValidator(settings.github_webhook_secret)
    # TODO: Inject proper idempotency store
    
    try:
        # Validate signature
        if not validator.validate(payload, x_hub_signature_256):
            raise WebhookValidationError()
        
        # Parse payload
        data = json.loads(payload)
        action = data.get("action", "")
        
        logger.info(
            "Received GitHub webhook",
            extra={
                "event": x_github_event,
                "action": action,
                "delivery_id": x_github_delivery,
            },
        )
        
        # Queue for processing based on event type
        if x_github_event == "workflow_run":
            # TODO: Queue Celery task
            pass
        elif x_github_event == "workflow_job":
            # TODO: Queue Celery task
            pass
        
        return JSONResponse(
            status_code=status.HTTP_202_ACCEPTED,
            content={
                "status": "queued",
                "delivery_id": x_github_delivery,
            },
        )
    
    except WebhookValidationError:
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={"detail": "Invalid webhook signature"},
        )
```

---

## Step 6: Create Tests

### 6.1 Test Configuration
Create `backend/tests/conftest.py`:

```python
"""Pytest configuration and fixtures."""
import asyncio
from collections.abc import AsyncGenerator, Generator
from typing import Any

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from testcontainers.postgres import PostgresContainer

from app.config import Settings, get_settings
from app.infrastructure.database.models.base import Base
from app.infrastructure.database.session import get_db
from app.main import create_app


@pytest.fixture(scope="session")
def event_loop() -> Generator[asyncio.AbstractEventLoop, None, None]:
    """Create event loop for async tests."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
def postgres_container() -> Generator[PostgresContainer, None, None]:
    """Start PostgreSQL container for tests."""
    with PostgresContainer(
        image="pgvector/pgvector:pg16",
        username="test",
        password="test",
        dbname="test_db",
    ) as postgres:
        yield postgres


@pytest.fixture(scope="session")
def test_settings(postgres_container: PostgresContainer) -> Settings:
    """Create test settings."""
    return Settings(
        environment="testing",
        postgres_user="test",
        postgres_password="test",
        postgres_host=postgres_container.get_container_host_ip(),
        postgres_port=int(postgres_container.get_exposed_port(5432)),
        postgres_db="test_db",
        github_token="test-token",
        github_webhook_secret="test-secret",
    )


@pytest_asyncio.fixture
async def db_session(
    test_settings: Settings,
) -> AsyncGenerator[AsyncSession, None]:
    """Create database session for tests."""
    engine = create_async_engine(test_settings.database_url, echo=False)
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as session:
        yield session
        await session.rollback()
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    
    await engine.dispose()


@pytest_asyncio.fixture
async def client(test_settings: Settings) -> AsyncGenerator[AsyncClient, None]:
    """Create test client."""
    app = create_app()
    app.dependency_overrides[get_settings] = lambda: test_settings
    
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        yield client
```

### 6.2 Test Result Parser Tests
Create `backend/tests/unit/application/services/test_test_result_parser.py`:

```python
"""Tests for test result parser."""
import pytest

from app.application.services.test_result_parser import (
    PytestParser,
    JestParser,
    GoTestParser,
    TestResultParserService,
    TestResult,
)


class TestPytestParser:
    """Tests for pytest log parsing."""
    
    @pytest.fixture
    def parser(self) -> PytestParser:
        return PytestParser()
    
    def test_can_parse_pytest_output(self, parser: PytestParser) -> None:
        """Should detect pytest output."""
        log = "collected 10 items\n===== 10 passed in 1.5s ====="
        assert parser.can_parse(log) is True
    
    def test_cannot_parse_jest_output(self, parser: PytestParser) -> None:
        """Should not detect Jest output."""
        log = "Tests: 10 passed, 10 total"
        assert parser.can_parse(log) is False
    
    def test_parse_success_only(self, parser: PytestParser) -> None:
        """Should parse successful test run."""
        log = """
        collected 10 items
        
        test_module.py ..........
        
        ===== 10 passed in 1.5s =====
        """
        result = parser.parse(log)
        
        assert result is not None
        assert result.framework == "pytest"
        assert result.total == 10
        assert result.passed == 10
        assert result.failed == 0
        assert result.skipped == 0
        assert result.duration_seconds == 1.5
    
    def test_parse_with_failures(self, parser: PytestParser) -> None:
        """Should parse test run with failures."""
        log = """
        collected 10 items
        
        ===== 2 failed, 7 passed, 1 skipped in 2.3s =====
        """
        result = parser.parse(log)
        
        assert result is not None
        assert result.total == 10
        assert result.passed == 7
        assert result.failed == 2
        assert result.skipped == 1
    
    def test_handles_docker_noise(self, parser: PytestParser) -> None:
        """Should parse despite Docker container prefixes."""
        log = """
        2024-01-15T10:00:00.000Z collected 5 items
        2024-01-15T10:00:01.000Z ===== 5 passed in 0.5s =====
        """
        result = parser.parse(log)
        
        assert result is not None
        assert result.passed == 5
    
    def test_handles_ansi_codes(self, parser: PytestParser) -> None:
        """Should parse despite ANSI color codes."""
        log = "\x1b[32mcollected 3 items\x1b[0m\n\x1b[32m===== 3 passed in 0.1s =====\x1b[0m"
        result = parser.parse(log)
        
        assert result is not None
        assert result.passed == 3


class TestJestParser:
    """Tests for Jest log parsing."""
    
    @pytest.fixture
    def parser(self) -> JestParser:
        return JestParser()
    
    def test_parse_success(self, parser: JestParser) -> None:
        """Should parse successful Jest run."""
        log = """
        PASS src/test.spec.js
        Tests: 5 passed, 5 total
        Time: 1.234s
        """
        result = parser.parse(log)
        
        assert result is not None
        assert result.framework == "jest"
        assert result.passed == 5
        assert result.total == 5
    
    def test_parse_with_failures(self, parser: JestParser) -> None:
        """Should parse Jest run with failures."""
        log = "Tests: 2 failed, 3 passed, 5 total"
        result = parser.parse(log)
        
        assert result is not None
        assert result.failed == 2
        assert result.passed == 3


class TestTestResultParserService:
    """Tests for parser orchestration."""
    
    @pytest.fixture
    def service(self) -> TestResultParserService:
        return TestResultParserService()
    
    def test_selects_pytest_parser(self, service: TestResultParserService) -> None:
        """Should select pytest parser for pytest output."""
        log = "collected 1 items\n===== 1 passed in 0.1s ====="
        result = service.parse(log)
        
        assert result is not None
        assert result.framework == "pytest"
    
    def test_selects_jest_parser(self, service: TestResultParserService) -> None:
        """Should select Jest parser for Jest output."""
        log = "Tests: 1 passed, 1 total"
        result = service.parse(log)
        
        assert result is not None
        assert result.framework == "jest"
    
    def test_returns_none_for_unknown(self, service: TestResultParserService) -> None:
        """Should return None for unrecognized output."""
        log = "This is not test output"
        result = service.parse(log)
        
        assert result is None
```

---

## Step 7: Create Docker Configuration

### 7.1 Backend Dockerfile
Create `backend/Dockerfile`:

```dockerfile
# Backend Dockerfile
FROM python:3.12-slim AS base

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install UV
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

WORKDIR /app

# Development stage
FROM base AS development

# Copy dependency files
COPY pyproject.toml uv.lock ./

# Install dependencies
RUN uv sync --frozen

# Copy application
COPY . .

# Create non-root user
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

ENV PATH="/app/.venv/bin:$PATH"

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]

# Production stage
FROM base AS production

# Copy dependency files
COPY pyproject.toml uv.lock ./

# Install production dependencies only
RUN uv sync --frozen --no-dev

# Copy application
COPY . .

# Create non-root user
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

ENV PATH="/app/.venv/bin:$PATH"

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### 7.2 Docker Compose
Create `docker-compose.yml` in project root:

```yaml
version: '3.9'

services:
  postgres:
    image: pgvector/pgvector:pg16
    container_name: gha-postgres
    environment:
      POSTGRES_USER: ${POSTGRES_USER:-gha}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD:-gha_secret}
      POSTGRES_DB: ${POSTGRES_DB:-github_actions}
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${POSTGRES_USER:-gha}"]
      interval: 10s
      timeout: 5s
      retries: 5

  redis:
    image: redis:7-alpine
    container_name: gha-redis
    command: redis-server --appendonly yes
    volumes:
      - redis_data:/data
    ports:
      - "6379:6379"
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5

  backend:
    build:
      context: ./backend
      target: development
    container_name: gha-backend
    environment:
      POSTGRES_USER: ${POSTGRES_USER:-gha}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD:-gha_secret}
      POSTGRES_HOST: postgres
      POSTGRES_PORT: 5432
      POSTGRES_DB: ${POSTGRES_DB:-github_actions}
      REDIS_URL: redis://redis:6379/0
      GITHUB_TOKEN: ${GITHUB_TOKEN:-}
      GITHUB_WEBHOOK_SECRET: ${GITHUB_WEBHOOK_SECRET:-}
      ANTHROPIC_API_KEY: ${ANTHROPIC_API_KEY:-}
      OPENAI_API_KEY: ${OPENAI_API_KEY:-}
      ENVIRONMENT: development
      LOG_LEVEL: DEBUG
    volumes:
      - ./backend:/app
    ports:
      - "8000:8000"
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy

  celery-worker:
    build:
      context: ./backend
      target: development
    container_name: gha-celery-worker
    command: uv run celery -A app.tasks.celery_app worker --loglevel=info
    environment:
      POSTGRES_USER: ${POSTGRES_USER:-gha}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD:-gha_secret}
      POSTGRES_HOST: postgres
      POSTGRES_PORT: 5432
      POSTGRES_DB: ${POSTGRES_DB:-github_actions}
      REDIS_URL: redis://redis:6379/0
      GITHUB_TOKEN: ${GITHUB_TOKEN:-}
      ANTHROPIC_API_KEY: ${ANTHROPIC_API_KEY:-}
      OPENAI_API_KEY: ${OPENAI_API_KEY:-}
    volumes:
      - ./backend:/app
    depends_on:
      - postgres
      - redis

  celery-beat:
    build:
      context: ./backend
      target: development
    container_name: gha-celery-beat
    command: uv run celery -A app.tasks.celery_app beat --loglevel=info
    environment:
      POSTGRES_USER: ${POSTGRES_USER:-gha}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD:-gha_secret}
      POSTGRES_HOST: postgres
      POSTGRES_PORT: 5432
      POSTGRES_DB: ${POSTGRES_DB:-github_actions}
      REDIS_URL: redis://redis:6379/0
      GITHUB_TOKEN: ${GITHUB_TOKEN:-}
    volumes:
      - ./backend:/app
    depends_on:
      - postgres
      - redis

volumes:
  postgres_data:
  redis_data:
```

---

## Next Steps

Continue with:
1. TESTING_GUIDE.md - Detailed testing requirements
2. ARCHITECTURE.md - Technical architecture deep dive
3. CLAUDE_CLI_PROMPTS.md - Ready-to-use prompts for implementation

"""Pytest configuration and fixtures."""

from collections.abc import AsyncGenerator
from typing import Any
from unittest.mock import AsyncMock, MagicMock

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from app.config import Settings, get_settings
from app.infrastructure.database.session import get_db
from app.main import create_app


@pytest.fixture
def test_settings() -> Settings:
    """Create test settings."""
    return Settings(
        environment="testing",
        postgres_user="test",
        postgres_password="test",
        postgres_host="localhost",
        postgres_port=5432,
        postgres_db="test_db",
        github_token="test-token",
        github_webhook_secret="test-webhook-secret",
        anthropic_api_key="test-anthropic-key",
        openai_api_key="test-openai-key",
    )


@pytest.fixture
def mock_db_session() -> AsyncMock:
    """Create a mock database session."""
    session = AsyncMock()
    return session


@pytest_asyncio.fixture
async def client(
    test_settings: Settings, mock_db_session: AsyncMock
) -> AsyncGenerator[AsyncClient, None]:
    """Create test HTTP client with mocked dependencies."""
    app = create_app()
    app.dependency_overrides[get_settings] = lambda: test_settings

    async def override_get_db() -> AsyncGenerator[AsyncMock, None]:
        yield mock_db_session

    app.dependency_overrides[get_db] = override_get_db

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        yield client


@pytest.fixture
def mock_github_client() -> AsyncMock:
    """Mocked GitHub client."""
    client = AsyncMock()
    client.get_workflow_runs.return_value = []
    client.get_jobs_for_run.return_value = []
    client.download_job_logs.return_value = ""
    return client


@pytest.fixture
def mock_llm_client() -> AsyncMock:
    """Mocked LLM client."""
    client = AsyncMock()
    client.analyze.return_value = {
        "root_cause": "Test failure",
        "error_summary": "Tests failed",
        "suggested_fixes": ["Fix the code"],
        "prevention_tips": ["Add more tests"],
        "confidence_score": 0.9,
    }
    return client


@pytest.fixture
def sample_workflow_run_payload() -> dict[str, Any]:
    """Sample GitHub workflow_run webhook payload."""
    return {
        "action": "completed",
        "workflow_run": {
            "id": 12345,
            "run_number": 42,
            "status": "completed",
            "conclusion": "success",
            "head_branch": "main",
            "head_sha": "abc123def456",
            "event": "push",
            "actor": {"login": "testuser"},
            "created_at": "2024-01-15T10:00:00Z",
            "updated_at": "2024-01-15T10:05:00Z",
        },
        "repository": {
            "id": 100,
            "name": "test-repo",
            "full_name": "org/test-repo",
            "owner": {"login": "org"},
        },
        "workflow": {
            "id": 200,
            "name": "CI",
            "path": ".github/workflows/ci.yml",
        },
    }


# Helper fixtures for creating mock model objects
@pytest.fixture
def mock_workflow() -> MagicMock:
    """Create a mock workflow object."""
    workflow = MagicMock()
    workflow.id = 1
    workflow.github_id = 12345
    workflow.name = "CI"
    workflow.path = ".github/workflows/ci.yml"
    workflow.state = "active"
    workflow.repo_id = 1
    return workflow


@pytest.fixture
def mock_workflow_run() -> MagicMock:
    """Create a mock workflow run object."""
    run = MagicMock()
    run.id = 1
    run.github_id = 123456
    run.run_number = 42
    run.status = "completed"
    run.conclusion = "success"
    run.head_branch = "main"
    run.head_sha = "abc123"
    run.event = "push"
    run.actor = "testuser"
    run.html_url = "https://github.com/org/repo/actions/runs/123456"
    run.workflow_id = 1
    run.run_started_at = None
    run.duration_seconds = 120
    run.jobs = []
    return run


@pytest.fixture
def mock_job() -> MagicMock:
    """Create a mock job object."""
    job = MagicMock()
    job.id = 1
    job.github_id = 654321
    job.name = "build"
    job.status = "completed"
    job.conclusion = "success"
    job.started_at = None
    job.completed_at = None
    job.runner_name = "ubuntu-latest"
    job.html_url = "https://github.com/org/repo/actions/runs/123/job/456"
    return job


@pytest.fixture
def mock_log() -> MagicMock:
    """Create a mock log object."""
    log = MagicMock()
    log.id = 1
    log.job_id = 1
    log.log_content = "Test log content"
    log.error_content = None
    log.log_size_bytes = 16
    log.category = None
    return log

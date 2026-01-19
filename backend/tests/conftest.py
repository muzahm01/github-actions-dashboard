"""Pytest configuration and fixtures."""
from collections.abc import AsyncGenerator
from typing import Any
from unittest.mock import AsyncMock

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from app.config import Settings, get_settings
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


@pytest_asyncio.fixture
async def client(test_settings: Settings) -> AsyncGenerator[AsyncClient, None]:
    """Create test HTTP client."""
    app = create_app()
    app.dependency_overrides[get_settings] = lambda: test_settings

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

"""Tests for GitHub API client."""

from datetime import UTC
from unittest.mock import MagicMock

import pytest

from app.config import Settings
from app.infrastructure.external.github_client import (
    GitHubClient,
    GitHubJob,
    GitHubRepository,
    GitHubWorkflow,
    GitHubWorkflowRun,
)

pytestmark = pytest.mark.unit


class TestGitHubClientInit:
    """Tests for GitHubClient initialization."""

    @pytest.fixture
    def mock_settings(self) -> MagicMock:
        """Create mock settings."""
        settings = MagicMock(spec=Settings)
        settings.github_token = "test-token"
        settings.github_api_base_url = "https://api.github.com"
        settings.github_org = "test-org"
        return settings

    def test_client_initialization(self, mock_settings: MagicMock) -> None:
        """Test client initializes correctly."""
        client = GitHubClient(mock_settings)
        assert client._token == "test-token"
        assert client._base_url == "https://api.github.com"
        assert client._org == "test-org"
        assert client._client is None


class TestGitHubDataClasses:
    """Tests for GitHub dataclasses."""

    def test_github_repository(self) -> None:
        """Test GitHubRepository dataclass."""
        repo = GitHubRepository(
            id=12345,
            name="test-repo",
            full_name="owner/test-repo",
            owner="owner",
            description="A test repository",
            default_branch="main",
        )
        assert repo.id == 12345
        assert repo.full_name == "owner/test-repo"

    def test_github_workflow(self) -> None:
        """Test GitHubWorkflow dataclass."""
        workflow = GitHubWorkflow(
            id=1,
            name="CI",
            path=".github/workflows/ci.yml",
            state="active",
        )
        assert workflow.id == 1
        assert workflow.name == "CI"

    def test_github_workflow_run(self) -> None:
        """Test GitHubWorkflowRun dataclass."""
        from datetime import datetime

        run = GitHubWorkflowRun(
            id=100,
            run_number=42,
            run_attempt=1,
            status="completed",
            conclusion="success",
            head_branch="main",
            head_sha="abc123",
            event="push",
            actor="developer",
            triggering_actor=None,
            html_url="https://github.com/owner/repo/actions/runs/100",
            created_at=datetime.now(tz=UTC),
            updated_at=datetime.now(tz=UTC),
            run_started_at=None,
        )
        assert run.id == 100
        assert run.status == "completed"

    def test_github_job(self) -> None:
        """Test GitHubJob dataclass."""
        job = GitHubJob(
            id=1,
            name="build",
            status="completed",
            conclusion="success",
            started_at=None,
            completed_at=None,
            runner_name="ubuntu-latest",
            runner_group=None,
            html_url="https://github.com/owner/repo/actions/runs/100/jobs/1",
            steps=[],
        )
        assert job.id == 1
        assert job.name == "build"
        assert job.conclusion == "success"

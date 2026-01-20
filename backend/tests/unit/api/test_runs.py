"""Tests for workflow run endpoints."""
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from httpx import AsyncClient


class TestListRuns:
    """Tests for GET /api/v1/runs/ endpoint."""

    @pytest.mark.asyncio
    async def test_list_runs_success(
        self, client: AsyncClient, mock_db_session: AsyncMock
    ) -> None:
        """Should return list of runs."""
        mock_run1 = MagicMock()
        mock_run1.id = 1
        mock_run1.github_id = 123456
        mock_run1.run_number = 42
        mock_run1.status = "completed"
        mock_run1.conclusion = "success"
        mock_run1.head_branch = "main"
        mock_run1.head_sha = "abc123"
        mock_run1.event = "push"
        mock_run1.actor = "testuser"
        mock_run1.html_url = "https://github.com/org/repo/actions/runs/123456"
        mock_run1.workflow_id = 1

        mock_run2 = MagicMock()
        mock_run2.id = 2
        mock_run2.github_id = 123457
        mock_run2.run_number = 43
        mock_run2.status = "completed"
        mock_run2.conclusion = "failure"
        mock_run2.head_branch = "feature"
        mock_run2.head_sha = "def456"
        mock_run2.event = "pull_request"
        mock_run2.actor = "testuser2"
        mock_run2.html_url = "https://github.com/org/repo/actions/runs/123457"
        mock_run2.workflow_id = 1

        with patch(
            "app.api.v1.runs.WorkflowRunRepository"
        ) as mock_repo_class:
            mock_repo = AsyncMock()
            mock_repo.get_all.return_value = [mock_run1, mock_run2]
            mock_repo.count.return_value = 2
            mock_repo_class.return_value = mock_repo

            response = await client.get("/api/v1/runs/")

        assert response.status_code == 200
        data = response.json()
        assert "runs" in data
        assert len(data["runs"]) == 2
        assert data["runs"][0]["run_number"] == 42
        assert data["runs"][1]["conclusion"] == "failure"
        assert data["total"] == 2

    @pytest.mark.asyncio
    async def test_list_runs_empty(
        self, client: AsyncClient, mock_db_session: AsyncMock
    ) -> None:
        """Should return empty list when no runs exist."""
        with patch(
            "app.api.v1.runs.WorkflowRunRepository"
        ) as mock_repo_class:
            mock_repo = AsyncMock()
            mock_repo.get_all.return_value = []
            mock_repo.count.return_value = 0
            mock_repo_class.return_value = mock_repo

            response = await client.get("/api/v1/runs/")

        assert response.status_code == 200
        data = response.json()
        assert data["runs"] == []
        assert data["total"] == 0

    @pytest.mark.asyncio
    async def test_list_runs_pagination(
        self, client: AsyncClient, mock_db_session: AsyncMock
    ) -> None:
        """Should support pagination parameters."""
        with patch(
            "app.api.v1.runs.WorkflowRunRepository"
        ) as mock_repo_class:
            mock_repo = AsyncMock()
            mock_repo.get_all.return_value = []
            mock_repo.count.return_value = 50
            mock_repo_class.return_value = mock_repo

            response = await client.get("/api/v1/runs/?limit=10&offset=20")

        assert response.status_code == 200
        mock_repo.get_all.assert_called_once_with(limit=10, offset=20)

    @pytest.mark.asyncio
    async def test_list_runs_filter_by_failure(
        self, client: AsyncClient, mock_db_session: AsyncMock
    ) -> None:
        """Should filter runs by failure conclusion when provided."""
        mock_run = MagicMock()
        mock_run.id = 1
        mock_run.github_id = 123456
        mock_run.run_number = 42
        mock_run.status = "completed"
        mock_run.conclusion = "failure"
        mock_run.head_branch = "main"
        mock_run.head_sha = "abc123"
        mock_run.event = "push"
        mock_run.actor = "testuser"
        mock_run.html_url = "https://github.com/org/repo/actions/runs/123456"
        mock_run.workflow_id = 1

        with patch(
            "app.api.v1.runs.WorkflowRunRepository"
        ) as mock_repo_class:
            mock_repo = AsyncMock()
            mock_repo.get_recent_failures.return_value = [mock_run]
            mock_repo_class.return_value = mock_repo

            response = await client.get("/api/v1/runs/?conclusion=failure")

        assert response.status_code == 200
        data = response.json()
        assert len(data["runs"]) == 1
        assert data["runs"][0]["conclusion"] == "failure"
        mock_repo.get_recent_failures.assert_called_once()


class TestGetRun:
    """Tests for GET /api/v1/runs/{run_id} endpoint."""

    @pytest.mark.asyncio
    async def test_get_run_success(
        self, client: AsyncClient, mock_db_session: AsyncMock
    ) -> None:
        """Should return run details with jobs when run exists."""
        mock_run = MagicMock()
        mock_run.id = 1
        mock_run.github_id = 123456
        mock_run.run_number = 42
        mock_run.status = "completed"
        mock_run.conclusion = "success"
        mock_run.head_branch = "main"
        mock_run.head_sha = "abc123"
        mock_run.event = "push"
        mock_run.actor = "testuser"
        mock_run.html_url = "https://github.com/org/repo/actions/runs/123456"
        mock_run.workflow_id = 1
        mock_run.run_started_at = None
        mock_run.duration_seconds = 120

        mock_job = MagicMock()
        mock_job.id = 10
        mock_job.github_id = 654321
        mock_job.name = "build"
        mock_job.status = "completed"
        mock_job.conclusion = "success"
        mock_run.jobs = [mock_job]

        with patch(
            "app.api.v1.runs.WorkflowRunRepository"
        ) as mock_repo_class:
            mock_repo = AsyncMock()
            mock_repo.get_with_jobs.return_value = mock_run
            mock_repo_class.return_value = mock_repo

            response = await client.get("/api/v1/runs/1")

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == 1
        assert data["run_number"] == 42
        assert data["status"] == "completed"
        assert "jobs" in data
        assert len(data["jobs"]) == 1
        assert data["jobs"][0]["name"] == "build"

    @pytest.mark.asyncio
    async def test_get_run_not_found(
        self, client: AsyncClient, mock_db_session: AsyncMock
    ) -> None:
        """Should return 404 when run does not exist."""
        with patch(
            "app.api.v1.runs.WorkflowRunRepository"
        ) as mock_repo_class:
            mock_repo = AsyncMock()
            mock_repo.get_with_jobs.return_value = None
            mock_repo_class.return_value = mock_repo

            response = await client.get("/api/v1/runs/999")

        assert response.status_code == 404
        data = response.json()
        assert "not found" in data["detail"].lower()

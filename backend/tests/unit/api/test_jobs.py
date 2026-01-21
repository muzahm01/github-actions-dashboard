"""Tests for job endpoints."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from httpx import AsyncClient


class TestGetJob:
    """Tests for GET /api/v1/jobs/{job_id} endpoint."""

    @pytest.mark.asyncio
    async def test_get_job_success(self, client: AsyncClient, mock_db_session: AsyncMock) -> None:
        """Should return job details when job exists."""
        mock_job = MagicMock()
        mock_job.id = 1
        mock_job.github_id = 123456
        mock_job.name = "build"
        mock_job.status = "completed"
        mock_job.conclusion = "success"
        mock_job.started_at = None
        mock_job.completed_at = None
        mock_job.runner_name = "ubuntu-latest"
        mock_job.html_url = "https://github.com/org/repo/actions/runs/123/job/456"

        with patch("app.api.v1.jobs.JobRepository") as mock_repo_class:
            mock_repo = AsyncMock()
            mock_repo.get_by_id.return_value = mock_job
            mock_repo_class.return_value = mock_repo

            response = await client.get("/api/v1/jobs/1")

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == 1
        assert data["name"] == "build"
        assert data["status"] == "completed"
        assert data["conclusion"] == "success"

    @pytest.mark.asyncio
    async def test_get_job_not_found(self, client: AsyncClient, mock_db_session: AsyncMock) -> None:
        """Should return 404 when job does not exist."""
        with patch("app.api.v1.jobs.JobRepository") as mock_repo_class:
            mock_repo = AsyncMock()
            mock_repo.get_by_id.return_value = None
            mock_repo_class.return_value = mock_repo

            response = await client.get("/api/v1/jobs/999")

        assert response.status_code == 404
        data = response.json()
        assert "not found" in data["detail"].lower()


class TestGetJobLogs:
    """Tests for GET /api/v1/jobs/{job_id}/logs endpoint."""

    @pytest.mark.asyncio
    async def test_get_job_logs_success(
        self, client: AsyncClient, mock_db_session: AsyncMock
    ) -> None:
        """Should return job logs when job exists."""
        mock_job = MagicMock()
        mock_job.id = 1

        mock_log = MagicMock()
        mock_log.id = 10
        mock_log.job_id = 1
        mock_log.log_content = "Test log content\nLine 2"
        mock_log.error_content = None
        mock_log.log_size_bytes = 25
        mock_log.category = None

        with (
            patch("app.api.v1.jobs.JobRepository") as mock_job_repo_class,
            patch("app.api.v1.jobs.LogRepository") as mock_log_repo_class,
        ):
            mock_job_repo = AsyncMock()
            mock_job_repo.get_by_id.return_value = mock_job
            mock_job_repo_class.return_value = mock_job_repo

            mock_log_repo = AsyncMock()
            mock_log_repo.get_by_job_id.return_value = [mock_log]
            mock_log_repo_class.return_value = mock_log_repo

            response = await client.get("/api/v1/jobs/1/logs")

        assert response.status_code == 200
        data = response.json()
        assert data["job_id"] == 1
        assert len(data["logs"]) == 1
        assert data["logs"][0]["log_content"] == "Test log content\nLine 2"

    @pytest.mark.asyncio
    async def test_get_job_logs_job_not_found(
        self, client: AsyncClient, mock_db_session: AsyncMock
    ) -> None:
        """Should return 404 when job does not exist."""
        with patch("app.api.v1.jobs.JobRepository") as mock_job_repo_class:
            mock_job_repo = AsyncMock()
            mock_job_repo.get_by_id.return_value = None
            mock_job_repo_class.return_value = mock_job_repo

            response = await client.get("/api/v1/jobs/999/logs")

        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_get_job_logs_empty(
        self, client: AsyncClient, mock_db_session: AsyncMock
    ) -> None:
        """Should return empty logs array when job has no logs."""
        mock_job = MagicMock()
        mock_job.id = 1

        with (
            patch("app.api.v1.jobs.JobRepository") as mock_job_repo_class,
            patch("app.api.v1.jobs.LogRepository") as mock_log_repo_class,
        ):
            mock_job_repo = AsyncMock()
            mock_job_repo.get_by_id.return_value = mock_job
            mock_job_repo_class.return_value = mock_job_repo

            mock_log_repo = AsyncMock()
            mock_log_repo.get_by_job_id.return_value = []
            mock_log_repo_class.return_value = mock_log_repo

            response = await client.get("/api/v1/jobs/1/logs")

        assert response.status_code == 200
        data = response.json()
        assert data["job_id"] == 1
        assert data["logs"] == []

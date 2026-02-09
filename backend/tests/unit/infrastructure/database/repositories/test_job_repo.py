"""Tests for job repository."""

from unittest.mock import AsyncMock, MagicMock

import pytest

from app.infrastructure.database.repositories.job_repo import JobRepository


pytestmark = pytest.mark.unit

class TestJobRepository:
    """Tests for JobRepository."""

    @pytest.fixture
    def mock_session(self) -> AsyncMock:
        """Create a mock async session."""
        session = AsyncMock()
        session.execute = AsyncMock()
        return session

    @pytest.fixture
    def repository(self, mock_session: AsyncMock) -> JobRepository:
        """Create a repository instance."""
        return JobRepository(mock_session)

    @pytest.mark.asyncio
    async def test_get_by_github_id(
        self, repository: JobRepository, mock_session: AsyncMock
    ) -> None:
        """Test getting job by GitHub ID."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = MagicMock(github_id=123)
        mock_session.execute.return_value = mock_result

        result = await repository.get_by_github_id(123)

        assert result is not None
        mock_session.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_by_run_id(self, repository: JobRepository, mock_session: AsyncMock) -> None:
        """Test getting jobs by workflow run ID."""
        mock_jobs = [MagicMock(run_id=1), MagicMock(run_id=1)]
        mock_result = MagicMock()
        mock_scalars = MagicMock()
        mock_scalars.all.return_value = mock_jobs
        mock_result.scalars.return_value = mock_scalars
        mock_session.execute.return_value = mock_result

        result = await repository.get_by_run_id(1)

        assert len(result) == 2
        mock_session.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_failed_jobs(
        self, repository: JobRepository, mock_session: AsyncMock
    ) -> None:
        """Test getting failed jobs for a run."""
        mock_jobs = [MagicMock(conclusion="failure")]
        mock_result = MagicMock()
        mock_scalars = MagicMock()
        mock_scalars.all.return_value = mock_jobs
        mock_result.scalars.return_value = mock_scalars
        mock_session.execute.return_value = mock_result

        result = await repository.get_failed_jobs(run_id=1)

        assert len(result) == 1
        mock_session.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_with_steps(self, repository: JobRepository, mock_session: AsyncMock) -> None:
        """Test getting job with steps."""
        mock_job = MagicMock(id=1, steps=[])
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_job
        mock_session.execute.return_value = mock_result

        result = await repository.get_with_steps(1)

        assert result is not None

    @pytest.mark.asyncio
    async def test_get_with_logs(self, repository: JobRepository, mock_session: AsyncMock) -> None:
        """Test getting job with logs."""
        mock_job = MagicMock(id=1, logs=[])
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_job
        mock_session.execute.return_value = mock_result

        result = await repository.get_with_logs(1)

        assert result is not None

    @pytest.mark.asyncio
    async def test_upsert_by_github_id_creates_new(
        self, repository: JobRepository, mock_session: AsyncMock
    ) -> None:
        """Test upsert creates new job when it doesn't exist."""

        # Mock get_by_github_id to return None (doesn't exist)
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_result

        job_data = {
            "github_id": 123,
            "run_id": 1,
            "name": "test-job",
            "status": "completed",
        }

        # Mock the add, flush, and refresh
        mock_session.add = MagicMock()
        mock_session.flush = AsyncMock()
        mock_session.refresh = AsyncMock()

        _result = await repository.upsert_by_github_id(job_data)

        # Verify create was called
        mock_session.add.assert_called_once()
        mock_session.flush.assert_called()

    @pytest.mark.asyncio
    async def test_upsert_by_github_id_updates_existing(
        self, repository: JobRepository, mock_session: AsyncMock
    ) -> None:
        """Test upsert updates existing job."""
        from app.infrastructure.database.models.job import Job

        # Create a mock existing job
        existing_job = MagicMock(spec=Job)
        existing_job.github_id = 123
        existing_job.name = "test-job"
        existing_job.status = "in_progress"

        # Mock get_by_github_id to return existing job
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = existing_job
        mock_session.execute.return_value = mock_result

        job_data = {
            "github_id": 123,
            "name": "test-job",
            "status": "completed",
        }

        mock_session.flush = AsyncMock()
        mock_session.refresh = AsyncMock()

        _result = await repository.upsert_by_github_id(job_data)

        # Verify update was called
        mock_session.flush.assert_called()
        assert existing_job.status == "completed"

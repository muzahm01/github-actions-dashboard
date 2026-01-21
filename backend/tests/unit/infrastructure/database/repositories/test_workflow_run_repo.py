"""Tests for workflow run repository."""

from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.infrastructure.database.repositories.workflow_run_repo import WorkflowRunRepository


class TestWorkflowRunRepository:
    """Tests for WorkflowRunRepository."""

    @pytest.fixture
    def mock_session(self) -> AsyncMock:
        """Create a mock async session."""
        session = AsyncMock()
        session.execute = AsyncMock()
        return session

    @pytest.fixture
    def repository(self, mock_session: AsyncMock) -> WorkflowRunRepository:
        """Create a repository instance."""
        return WorkflowRunRepository(mock_session)

    @pytest.mark.asyncio
    async def test_get_by_github_id(
        self, repository: WorkflowRunRepository, mock_session: AsyncMock
    ) -> None:
        """Test getting workflow run by GitHub ID."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = MagicMock(github_id=123)
        mock_session.execute.return_value = mock_result

        result = await repository.get_by_github_id(123)

        assert result is not None
        mock_session.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_by_workflow_id(
        self, repository: WorkflowRunRepository, mock_session: AsyncMock
    ) -> None:
        """Test getting runs by workflow ID."""
        mock_runs = [MagicMock(workflow_id=1), MagicMock(workflow_id=1)]
        mock_result = MagicMock()
        mock_scalars = MagicMock()
        mock_scalars.all.return_value = mock_runs
        mock_result.scalars.return_value = mock_scalars
        mock_session.execute.return_value = mock_result

        result = await repository.get_by_workflow_id(1)

        assert len(result) == 2

    @pytest.mark.asyncio
    async def test_get_recent_failures(
        self, repository: WorkflowRunRepository, mock_session: AsyncMock
    ) -> None:
        """Test getting recent failures."""
        mock_runs = [MagicMock(conclusion="failure")]
        mock_result = MagicMock()
        mock_scalars = MagicMock()
        mock_scalars.all.return_value = mock_runs
        mock_result.scalars.return_value = mock_scalars
        mock_session.execute.return_value = mock_result

        result = await repository.get_recent_failures(limit=10)

        assert len(result) == 1
        mock_session.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_runs_in_timerange(
        self, repository: WorkflowRunRepository, mock_session: AsyncMock
    ) -> None:
        """Test getting runs by date range."""
        start = datetime(2024, 1, 1, tzinfo=UTC)
        end = datetime(2024, 1, 31, tzinfo=UTC)
        mock_runs = [MagicMock(), MagicMock()]
        mock_result = MagicMock()
        mock_scalars = MagicMock()
        mock_scalars.all.return_value = mock_runs
        mock_result.scalars.return_value = mock_scalars
        mock_session.execute.return_value = mock_result

        result = await repository.get_runs_in_timerange(start, end)

        assert len(result) == 2
        mock_session.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_by_branch(
        self, repository: WorkflowRunRepository, mock_session: AsyncMock
    ) -> None:
        """Test getting runs by branch."""
        mock_runs = [MagicMock(head_branch="main")]
        mock_result = MagicMock()
        mock_scalars = MagicMock()
        mock_scalars.all.return_value = mock_runs
        mock_result.scalars.return_value = mock_scalars
        mock_session.execute.return_value = mock_result

        result = await repository.get_by_branch(1, "main")

        assert len(result) == 1

    @pytest.mark.asyncio
    async def test_get_with_jobs(
        self, repository: WorkflowRunRepository, mock_session: AsyncMock
    ) -> None:
        """Test getting run with jobs."""
        mock_run = MagicMock(id=1, jobs=[])
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_run
        mock_session.execute.return_value = mock_result

        result = await repository.get_with_jobs(1)

        assert result is not None

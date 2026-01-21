"""Tests for workflow repository."""

from unittest.mock import AsyncMock, MagicMock

import pytest

from app.infrastructure.database.repositories.workflow_repo import WorkflowRepository


class TestWorkflowRepository:
    """Tests for WorkflowRepository."""

    @pytest.fixture
    def mock_session(self) -> AsyncMock:
        """Create a mock async session."""
        session = AsyncMock()
        session.execute = AsyncMock()
        return session

    @pytest.fixture
    def repository(self, mock_session: AsyncMock) -> WorkflowRepository:
        """Create a repository instance."""
        return WorkflowRepository(mock_session)

    @pytest.mark.asyncio
    async def test_get_by_github_id(
        self, repository: WorkflowRepository, mock_session: AsyncMock
    ) -> None:
        """Test getting workflow by GitHub ID."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = MagicMock(github_id=123)
        mock_session.execute.return_value = mock_result

        result = await repository.get_by_github_id(123)

        assert result is not None
        mock_session.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_by_repo_id(
        self, repository: WorkflowRepository, mock_session: AsyncMock
    ) -> None:
        """Test getting workflows by repository ID."""
        mock_workflows = [MagicMock(repo_id=1), MagicMock(repo_id=1)]
        mock_result = MagicMock()
        mock_scalars = MagicMock()
        mock_scalars.all.return_value = mock_workflows
        mock_result.scalars.return_value = mock_scalars
        mock_session.execute.return_value = mock_result

        result = await repository.get_by_repo_id(1)

        assert len(result) == 2
        mock_session.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_with_runs(
        self, repository: WorkflowRepository, mock_session: AsyncMock
    ) -> None:
        """Test getting workflow with runs."""
        mock_workflow = MagicMock(id=1, workflow_runs=[])
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_workflow
        mock_session.execute.return_value = mock_result

        result = await repository.get_with_runs(1)

        assert result is not None
        mock_session.execute.assert_called_once()

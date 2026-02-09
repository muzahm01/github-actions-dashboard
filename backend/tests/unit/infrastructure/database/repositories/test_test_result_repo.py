"""Tests for test result repository."""

from unittest.mock import AsyncMock, MagicMock

import pytest

from app.infrastructure.database.repositories.test_result_repo import TestResultRepository


pytestmark = pytest.mark.unit

class TestTestResultRepository:
    """Tests for TestResultRepository."""

    @pytest.fixture
    def mock_session(self) -> AsyncMock:
        """Create a mock async session."""
        session = AsyncMock()
        session.execute = AsyncMock()
        session.commit = AsyncMock()
        session.refresh = AsyncMock()
        return session

    @pytest.fixture
    def repository(self, mock_session: AsyncMock) -> TestResultRepository:
        """Create a repository instance."""
        return TestResultRepository(mock_session)

    @pytest.mark.asyncio
    async def test_get_by_log_id(
        self, repository: TestResultRepository, mock_session: AsyncMock
    ) -> None:
        """Test getting test results by log ID."""
        mock_results = [MagicMock(log_id=1), MagicMock(log_id=1)]
        mock_result = MagicMock()
        mock_scalars = MagicMock()
        mock_scalars.all.return_value = mock_results
        mock_result.scalars.return_value = mock_scalars
        mock_session.execute.return_value = mock_result

        result = await repository.get_by_log_id(1)

        assert len(result) == 2
        mock_session.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_by_framework(
        self, repository: TestResultRepository, mock_session: AsyncMock
    ) -> None:
        """Test getting test results by framework."""
        mock_results = [MagicMock(framework="pytest"), MagicMock(framework="pytest")]
        mock_result = MagicMock()
        mock_scalars = MagicMock()
        mock_scalars.all.return_value = mock_results
        mock_result.scalars.return_value = mock_scalars
        mock_session.execute.return_value = mock_result

        result = await repository.get_by_framework("pytest", limit=50)

        assert len(result) == 2
        mock_session.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_failed_tests(
        self, repository: TestResultRepository, mock_session: AsyncMock
    ) -> None:
        """Test getting test results with failures."""
        mock_results = [MagicMock(failed=5), MagicMock(failed=3)]
        mock_result = MagicMock()
        mock_scalars = MagicMock()
        mock_scalars.all.return_value = mock_results
        mock_result.scalars.return_value = mock_scalars
        mock_session.execute.return_value = mock_result

        result = await repository.get_failed_tests(limit=50)

        assert len(result) == 2
        mock_session.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_recent(
        self, repository: TestResultRepository, mock_session: AsyncMock
    ) -> None:
        """Test getting recent test results."""
        mock_results = [MagicMock(), MagicMock(), MagicMock()]
        mock_result = MagicMock()
        mock_scalars = MagicMock()
        mock_scalars.all.return_value = mock_results
        mock_result.scalars.return_value = mock_scalars
        mock_session.execute.return_value = mock_result

        result = await repository.get_recent(limit=20)

        assert len(result) == 3
        mock_session.execute.assert_called_once()

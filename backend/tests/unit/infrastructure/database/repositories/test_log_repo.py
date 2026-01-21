"""Tests for log repository."""

from unittest.mock import AsyncMock, MagicMock

import pytest

from app.infrastructure.database.repositories.log_repo import LogRepository


class TestLogRepository:
    """Tests for LogRepository."""

    @pytest.fixture
    def mock_session(self) -> AsyncMock:
        """Create a mock async session."""
        session = AsyncMock()
        session.execute = AsyncMock()
        return session

    @pytest.fixture
    def repository(self, mock_session: AsyncMock) -> LogRepository:
        """Create a repository instance."""
        return LogRepository(mock_session)

    @pytest.mark.asyncio
    async def test_get_by_job_id(self, repository: LogRepository, mock_session: AsyncMock) -> None:
        """Test getting logs by job ID."""
        mock_logs = [MagicMock(job_id=1), MagicMock(job_id=1)]
        mock_result = MagicMock()
        mock_scalars = MagicMock()
        mock_scalars.all.return_value = mock_logs
        mock_result.scalars.return_value = mock_scalars
        mock_session.execute.return_value = mock_result

        result = await repository.get_by_job_id(1)

        assert len(result) == 2
        mock_session.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_by_hash(self, repository: LogRepository, mock_session: AsyncMock) -> None:
        """Test getting log by hash."""
        mock_log = MagicMock(log_hash="abc123")
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_log
        mock_session.execute.return_value = mock_result

        result = await repository.get_by_hash("abc123")

        assert result is not None
        mock_session.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_by_hash_not_found(
        self, repository: LogRepository, mock_session: AsyncMock
    ) -> None:
        """Test getting log by hash when not found."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_result

        result = await repository.get_by_hash("nonexistent")

        assert result is None

    @pytest.mark.asyncio
    async def test_get_logs_with_errors(
        self, repository: LogRepository, mock_session: AsyncMock
    ) -> None:
        """Test getting logs with errors."""
        mock_logs = [MagicMock(error_content="error")]
        mock_result = MagicMock()
        mock_scalars = MagicMock()
        mock_scalars.all.return_value = mock_logs
        mock_result.scalars.return_value = mock_scalars
        mock_session.execute.return_value = mock_result

        result = await repository.get_logs_with_errors(limit=10)

        assert len(result) == 1
        mock_session.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_by_category(
        self, repository: LogRepository, mock_session: AsyncMock
    ) -> None:
        """Test getting logs by category."""
        mock_logs = [MagicMock(category="test_failure")]
        mock_result = MagicMock()
        mock_scalars = MagicMock()
        mock_scalars.all.return_value = mock_logs
        mock_result.scalars.return_value = mock_scalars
        mock_session.execute.return_value = mock_result

        result = await repository.get_by_category("test_failure")

        assert len(result) == 1
        mock_session.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_find_similar_by_embedding(
        self, repository: LogRepository, mock_session: AsyncMock
    ) -> None:
        """Test finding similar logs by embedding."""
        embedding = [0.1] * 1536

        # Mock the raw SQL result
        mock_row = MagicMock()
        mock_row.id = 1
        mock_row.similarity = 0.95
        mock_result = MagicMock()
        mock_result.fetchall.return_value = [mock_row]
        mock_session.execute.return_value = mock_result

        # Mock get_by_id to return a log
        mock_log = MagicMock(id=1)
        original_get_by_id = repository.get_by_id
        repository.get_by_id = AsyncMock(return_value=mock_log)

        result = await repository.find_similar_by_embedding(embedding, limit=5)

        assert len(result) == 1
        assert result[0][0] == mock_log
        assert result[0][1] == 0.95

        # Restore
        repository.get_by_id = original_get_by_id

    @pytest.mark.asyncio
    async def test_search_by_content(
        self, repository: LogRepository, mock_session: AsyncMock
    ) -> None:
        """Test searching logs by content."""
        mock_logs = [MagicMock(log_content="error message")]
        mock_result = MagicMock()
        mock_scalars = MagicMock()
        mock_scalars.all.return_value = mock_logs
        mock_result.scalars.return_value = mock_scalars
        mock_session.execute.return_value = mock_result

        result = await repository.search_by_content("error")

        assert len(result) == 1
        mock_session.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_embedding(
        self, repository: LogRepository, mock_session: AsyncMock
    ) -> None:
        """Test updating log embedding."""
        mock_log = MagicMock(id=1, embedding=None)
        embedding = [0.1] * 1536

        # Mock get_by_id
        original_get_by_id = repository.get_by_id
        repository.get_by_id = AsyncMock(return_value=mock_log)

        # Mock update
        original_update = repository.update
        repository.update = AsyncMock(return_value=mock_log)

        result = await repository.update_embedding(1, embedding)

        assert result == mock_log
        repository.get_by_id.assert_called_once_with(1)
        repository.update.assert_called_once()

        # Restore
        repository.get_by_id = original_get_by_id
        repository.update = original_update

    @pytest.mark.asyncio
    async def test_update_embedding_not_found(
        self, repository: LogRepository, mock_session: AsyncMock
    ) -> None:
        """Test updating embedding for non-existent log."""
        embedding = [0.1] * 1536

        # Mock get_by_id returning None
        original_get_by_id = repository.get_by_id
        repository.get_by_id = AsyncMock(return_value=None)

        result = await repository.update_embedding(999, embedding)

        assert result is None

        # Restore
        repository.get_by_id = original_get_by_id

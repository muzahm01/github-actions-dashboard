"""Tests for error analysis repository."""

from unittest.mock import AsyncMock, MagicMock

import pytest

from app.infrastructure.database.repositories.error_analysis_repo import (
    ErrorAnalysisRepository,
)


class TestErrorAnalysisRepository:
    """Tests for ErrorAnalysisRepository."""

    @pytest.fixture
    def mock_session(self) -> AsyncMock:
        """Create a mock async session."""
        session = AsyncMock()
        session.execute = AsyncMock()
        return session

    @pytest.fixture
    def repository(self, mock_session: AsyncMock) -> ErrorAnalysisRepository:
        """Create a repository instance."""
        return ErrorAnalysisRepository(mock_session)

    @pytest.mark.asyncio
    async def test_get_by_log_id(
        self, repository: ErrorAnalysisRepository, mock_session: AsyncMock
    ) -> None:
        """Test getting analysis by log ID."""
        mock_analysis = MagicMock(log_id=1)
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_analysis
        mock_session.execute.return_value = mock_result

        result = await repository.get_by_log_id(1)

        assert result is not None
        assert result.log_id == 1
        mock_session.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_by_log_id_not_found(
        self, repository: ErrorAnalysisRepository, mock_session: AsyncMock
    ) -> None:
        """Test getting analysis by log ID when not found."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_result

        result = await repository.get_by_log_id(999)

        assert result is None

    @pytest.mark.asyncio
    async def test_get_recent(
        self, repository: ErrorAnalysisRepository, mock_session: AsyncMock
    ) -> None:
        """Test getting recent analyses."""
        mock_analyses = [MagicMock(id=1), MagicMock(id=2)]
        mock_result = MagicMock()
        mock_scalars = MagicMock()
        mock_scalars.all.return_value = mock_analyses
        mock_result.scalars.return_value = mock_scalars
        mock_session.execute.return_value = mock_result

        result = await repository.get_recent(limit=2)

        assert len(result) == 2
        mock_session.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_recent_with_default_limit(
        self, repository: ErrorAnalysisRepository, mock_session: AsyncMock
    ) -> None:
        """Test getting recent analyses with default limit."""
        mock_analyses = [MagicMock(id=i) for i in range(20)]
        mock_result = MagicMock()
        mock_scalars = MagicMock()
        mock_scalars.all.return_value = mock_analyses
        mock_result.scalars.return_value = mock_scalars
        mock_session.execute.return_value = mock_result

        result = await repository.get_recent()

        assert len(result) == 20
        mock_session.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_find_similar_by_embedding(
        self, repository: ErrorAnalysisRepository, mock_session: AsyncMock
    ) -> None:
        """Test finding similar analyses by embedding."""
        embedding = [0.1] * 1536

        # Mock the raw SQL result
        mock_row = MagicMock()
        mock_row.id = 1
        mock_row.similarity = 0.85
        mock_result = MagicMock()
        mock_result.fetchall.return_value = [mock_row]
        mock_session.execute.return_value = mock_result

        # Mock get_by_id to return an analysis
        mock_analysis = MagicMock(id=1)
        original_get_by_id = repository.get_by_id
        repository.get_by_id = AsyncMock(return_value=mock_analysis)

        result = await repository.find_similar_by_embedding(embedding, limit=5, threshold=0.7)

        assert len(result) == 1
        assert result[0][0] == mock_analysis
        assert result[0][1] == 0.85

        # Restore
        repository.get_by_id = original_get_by_id

    @pytest.mark.asyncio
    async def test_find_similar_by_embedding_with_defaults(
        self, repository: ErrorAnalysisRepository, mock_session: AsyncMock
    ) -> None:
        """Test finding similar analyses with default parameters."""
        embedding = [0.1] * 1536

        # Mock the raw SQL result
        mock_result = MagicMock()
        mock_result.fetchall.return_value = []
        mock_session.execute.return_value = mock_result

        result = await repository.find_similar_by_embedding(embedding)

        assert len(result) == 0

    @pytest.mark.asyncio
    async def test_find_similar_by_embedding_filters_none_results(
        self, repository: ErrorAnalysisRepository, mock_session: AsyncMock
    ) -> None:
        """Test that find_similar_by_embedding filters out None results."""
        embedding = [0.1] * 1536

        # Mock the raw SQL result with an ID that doesn't exist
        mock_row = MagicMock()
        mock_row.id = 999
        mock_row.similarity = 0.85
        mock_result = MagicMock()
        mock_result.fetchall.return_value = [mock_row]
        mock_session.execute.return_value = mock_result

        # Mock get_by_id to return None (analysis not found)
        original_get_by_id = repository.get_by_id
        repository.get_by_id = AsyncMock(return_value=None)

        result = await repository.find_similar_by_embedding(embedding)

        assert len(result) == 0

        # Restore
        repository.get_by_id = original_get_by_id

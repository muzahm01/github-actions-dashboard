"""Tests for repository repository."""

from unittest.mock import AsyncMock, MagicMock

import pytest

from app.infrastructure.database.repositories.repository_repo import RepositoryRepository


class TestRepositoryRepository:
    """Tests for RepositoryRepository."""

    @pytest.fixture
    def mock_session(self) -> AsyncMock:
        """Create a mock async session."""
        session = AsyncMock()
        session.execute = AsyncMock()
        session.commit = AsyncMock()
        session.refresh = AsyncMock()
        return session

    @pytest.fixture
    def repository(self, mock_session: AsyncMock) -> RepositoryRepository:
        """Create a repository instance."""
        return RepositoryRepository(mock_session)

    @pytest.mark.asyncio
    async def test_get_by_github_id(
        self, repository: RepositoryRepository, mock_session: AsyncMock
    ) -> None:
        """Test getting repository by GitHub ID."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = MagicMock(github_id=12345)
        mock_session.execute.return_value = mock_result

        result = await repository.get_by_github_id(12345)

        assert result is not None
        mock_session.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_by_github_id_not_found(
        self, repository: RepositoryRepository, mock_session: AsyncMock
    ) -> None:
        """Test getting repository by GitHub ID when not found."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_result

        result = await repository.get_by_github_id(99999)

        assert result is None

    @pytest.mark.asyncio
    async def test_get_by_full_name(
        self, repository: RepositoryRepository, mock_session: AsyncMock
    ) -> None:
        """Test getting repository by full name."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = MagicMock(full_name="owner/repo")
        mock_session.execute.return_value = mock_result

        result = await repository.get_by_full_name("owner/repo")

        assert result is not None
        mock_session.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_active(
        self, repository: RepositoryRepository, mock_session: AsyncMock
    ) -> None:
        """Test getting active repositories."""
        mock_repos = [MagicMock(is_active=True), MagicMock(is_active=True)]
        mock_result = MagicMock()
        mock_scalars = MagicMock()
        mock_scalars.all.return_value = mock_repos
        mock_result.scalars.return_value = mock_scalars
        mock_session.execute.return_value = mock_result

        result = await repository.get_active()

        assert len(result) == 2
        mock_session.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_by_owner(
        self, repository: RepositoryRepository, mock_session: AsyncMock
    ) -> None:
        """Test getting repositories by owner."""
        mock_repos = [MagicMock(owner="test-org")]
        mock_result = MagicMock()
        mock_scalars = MagicMock()
        mock_scalars.all.return_value = mock_repos
        mock_result.scalars.return_value = mock_scalars
        mock_session.execute.return_value = mock_result

        result = await repository.get_by_owner("test-org")

        assert len(result) == 1
        mock_session.execute.assert_called_once()

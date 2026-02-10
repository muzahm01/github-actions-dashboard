"""Tests for repository repository."""

from unittest.mock import AsyncMock, MagicMock

import pytest

from app.infrastructure.database.repositories.repository_repo import RepositoryRepository


pytestmark = pytest.mark.unit

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

    @pytest.mark.asyncio
    async def test_upsert_by_github_id_creates_new(
        self, repository: RepositoryRepository, mock_session: AsyncMock
    ) -> None:
        """Test upsert creates new repository when it doesn't exist."""

        # Mock get_by_github_id to return None (doesn't exist)
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_result

        repo_data = {
            "github_id": 12345,
            "full_name": "owner/repo",
            "owner": "owner",
            "name": "repo",
        }

        # Mock the add, flush, and refresh
        mock_session.add = MagicMock()
        mock_session.flush = AsyncMock()
        mock_session.refresh = AsyncMock()

        _result = await repository.upsert_by_github_id(repo_data)

        # Verify create was called
        mock_session.add.assert_called_once()
        mock_session.flush.assert_called()

    @pytest.mark.asyncio
    async def test_upsert_by_github_id_updates_existing(
        self, repository: RepositoryRepository, mock_session: AsyncMock
    ) -> None:
        """Test upsert updates existing repository."""
        from app.infrastructure.database.models.repository import Repository

        # Create a mock existing repository
        existing_repo = MagicMock(spec=Repository)
        existing_repo.github_id = 12345
        existing_repo.full_name = "owner/repo"
        existing_repo.owner = "owner"
        existing_repo.name = "repo"

        # Mock get_by_github_id to return existing repo
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = existing_repo
        mock_session.execute.return_value = mock_result

        repo_data = {
            "github_id": 12345,
            "full_name": "owner/new-repo",
            "owner": "owner",
            "name": "new-repo",
        }

        # Mock flush and refresh
        mock_session.flush = AsyncMock()
        mock_session.refresh = AsyncMock()

        _result = await repository.upsert_by_github_id(repo_data)

        # Verify update was called
        mock_session.flush.assert_called()
        assert existing_repo.full_name == "owner/new-repo"
        assert existing_repo.name == "new-repo"

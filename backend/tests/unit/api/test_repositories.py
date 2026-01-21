"""Tests for repositories API endpoints."""

from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from httpx import AsyncClient


class TestRepositoriesRouter:
    """Tests for repositories router configuration."""

    def test_router_has_list_endpoint(self) -> None:
        """Should have list repositories endpoint."""
        from app.api.v1.repositories import router

        routes = [route.path for route in router.routes]
        assert "/" in routes

    def test_router_has_get_endpoint(self) -> None:
        """Should have get repository endpoint."""
        from app.api.v1.repositories import router

        routes = [route.path for route in router.routes]
        assert "/{repository_id}" in routes

    def test_router_has_activate_endpoint(self) -> None:
        """Should have activate repository endpoint."""
        from app.api.v1.repositories import router

        routes = [route.path for route in router.routes]
        assert "/{repository_id}/activate" in routes

    def test_router_has_deactivate_endpoint(self) -> None:
        """Should have deactivate repository endpoint."""
        from app.api.v1.repositories import router

        routes = [route.path for route in router.routes]
        assert "/{repository_id}/deactivate" in routes

    def test_router_has_correct_number_of_routes(self) -> None:
        """Should have expected number of routes."""
        from app.api.v1.repositories import router

        # 4 routes: list, get, activate, deactivate
        assert len(router.routes) == 4


@pytest.fixture
def mock_repository() -> MagicMock:
    """Create a mock repository object."""
    repo = MagicMock()
    repo.id = 1
    repo.github_id = 12345
    repo.name = "test-repo"
    repo.full_name = "org/test-repo"
    repo.owner = "org"
    repo.description = "A test repository"
    repo.is_active = True
    repo.webhook_configured = False
    repo.last_synced_at = datetime.now(UTC)
    repo.created_at = datetime.now(UTC)
    return repo


class TestListRepositories:
    """Tests for list_repositories endpoint."""

    @pytest.mark.asyncio
    async def test_returns_list(
        self, client: AsyncClient, mock_db_session: MagicMock, mock_repository: MagicMock
    ) -> None:
        """Should return list of repositories."""
        with patch("app.api.v1.repositories.RepositoryRepository") as mock_repo_class:
            mock_repo = AsyncMock()
            mock_repo.get_all.return_value = [mock_repository]
            mock_repo_class.return_value = mock_repo

            response = await client.get("/api/v1/repositories/")

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 1
        assert data[0]["name"] == "test-repo"

    @pytest.mark.asyncio
    async def test_returns_empty_list(
        self, client: AsyncClient, mock_db_session: MagicMock
    ) -> None:
        """Should return empty list when no repositories."""
        with patch("app.api.v1.repositories.RepositoryRepository") as mock_repo_class:
            mock_repo = AsyncMock()
            mock_repo.get_all.return_value = []
            mock_repo_class.return_value = mock_repo

            response = await client.get("/api/v1/repositories/")

        assert response.status_code == 200
        data = response.json()
        assert data == []

    @pytest.mark.asyncio
    async def test_with_active_only_filter(
        self, client: AsyncClient, mock_db_session: MagicMock, mock_repository: MagicMock
    ) -> None:
        """Should filter active repositories only."""
        with patch("app.api.v1.repositories.RepositoryRepository") as mock_repo_class:
            mock_repo = AsyncMock()
            mock_repo.get_active.return_value = [mock_repository]
            mock_repo_class.return_value = mock_repo

            response = await client.get("/api/v1/repositories/?active_only=true")

        assert response.status_code == 200
        mock_repo.get_active.assert_called_once()


class TestGetRepository:
    """Tests for get_repository endpoint."""

    @pytest.mark.asyncio
    async def test_returns_repository(
        self, client: AsyncClient, mock_db_session: MagicMock, mock_repository: MagicMock
    ) -> None:
        """Should return repository details."""
        with patch("app.api.v1.repositories.RepositoryRepository") as mock_repo_class:
            mock_repo = AsyncMock()
            mock_repo.get_by_id.return_value = mock_repository
            mock_repo_class.return_value = mock_repo

            response = await client.get("/api/v1/repositories/1")

        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "test-repo"
        assert data["full_name"] == "org/test-repo"

    @pytest.mark.asyncio
    async def test_returns_404_for_missing(
        self, client: AsyncClient, mock_db_session: MagicMock
    ) -> None:
        """Should return 404 for non-existent repository."""
        with patch("app.api.v1.repositories.RepositoryRepository") as mock_repo_class:
            mock_repo = AsyncMock()
            mock_repo.get_by_id.return_value = None
            mock_repo_class.return_value = mock_repo

            response = await client.get("/api/v1/repositories/999")

        assert response.status_code == 404


class TestActivateRepository:
    """Tests for activate_repository endpoint."""

    @pytest.mark.asyncio
    async def test_activates_repository(
        self, client: AsyncClient, mock_db_session: MagicMock, mock_repository: MagicMock
    ) -> None:
        """Should activate a repository."""
        with patch("app.api.v1.repositories.RepositoryRepository") as mock_repo_class:
            mock_repo = AsyncMock()
            mock_repo.get_by_id.return_value = mock_repository
            mock_repo.update.return_value = mock_repository
            mock_repo_class.return_value = mock_repo

            response = await client.post("/api/v1/repositories/1/activate")

        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "Repository activated"

    @pytest.mark.asyncio
    async def test_returns_404_for_missing(
        self, client: AsyncClient, mock_db_session: MagicMock
    ) -> None:
        """Should return 404 for non-existent repository."""
        with patch("app.api.v1.repositories.RepositoryRepository") as mock_repo_class:
            mock_repo = AsyncMock()
            mock_repo.get_by_id.return_value = None
            mock_repo_class.return_value = mock_repo

            response = await client.post("/api/v1/repositories/999/activate")

        assert response.status_code == 404


class TestDeactivateRepository:
    """Tests for deactivate_repository endpoint."""

    @pytest.mark.asyncio
    async def test_deactivates_repository(
        self, client: AsyncClient, mock_db_session: MagicMock, mock_repository: MagicMock
    ) -> None:
        """Should deactivate a repository."""
        with patch("app.api.v1.repositories.RepositoryRepository") as mock_repo_class:
            mock_repo = AsyncMock()
            mock_repo.get_by_id.return_value = mock_repository
            mock_repo.update.return_value = mock_repository
            mock_repo_class.return_value = mock_repo

            response = await client.post("/api/v1/repositories/1/deactivate")

        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "Repository deactivated"

    @pytest.mark.asyncio
    async def test_returns_404_for_missing(
        self, client: AsyncClient, mock_db_session: MagicMock
    ) -> None:
        """Should return 404 for non-existent repository."""
        with patch("app.api.v1.repositories.RepositoryRepository") as mock_repo_class:
            mock_repo = AsyncMock()
            mock_repo.get_by_id.return_value = None
            mock_repo_class.return_value = mock_repo

            response = await client.post("/api/v1/repositories/999/deactivate")

        assert response.status_code == 404

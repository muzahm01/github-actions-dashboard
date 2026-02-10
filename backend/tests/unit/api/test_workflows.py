"""Tests for workflow endpoints."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from httpx import AsyncClient


pytestmark = pytest.mark.unit

class TestListWorkflows:
    """Tests for GET /api/v1/workflows/ endpoint."""

    @pytest.mark.asyncio
    async def test_list_workflows_success(
        self, client: AsyncClient, mock_db_session: AsyncMock
    ) -> None:
        """Should return list of workflows."""
        mock_workflow1 = MagicMock()
        mock_workflow1.id = 1
        mock_workflow1.github_id = 12345
        mock_workflow1.name = "CI"
        mock_workflow1.path = ".github/workflows/ci.yml"
        mock_workflow1.state = "active"
        mock_workflow1.repo_id = 1

        mock_workflow2 = MagicMock()
        mock_workflow2.id = 2
        mock_workflow2.github_id = 12346
        mock_workflow2.name = "Deploy"
        mock_workflow2.path = ".github/workflows/deploy.yml"
        mock_workflow2.state = "active"
        mock_workflow2.repo_id = 1

        with patch("app.application.services.workflow_query_service.WorkflowRepository") as mock_repo_class:
            mock_repo = AsyncMock()
            mock_repo.get_all.return_value = [mock_workflow1, mock_workflow2]
            mock_repo.count.return_value = 2
            mock_repo_class.return_value = mock_repo

            response = await client.get("/api/v1/workflows/")

        assert response.status_code == 200
        data = response.json()
        assert "workflows" in data
        assert len(data["workflows"]) == 2
        assert data["workflows"][0]["name"] == "CI"
        assert data["workflows"][1]["name"] == "Deploy"
        assert data["total"] == 2

    @pytest.mark.asyncio
    async def test_list_workflows_empty(
        self, client: AsyncClient, mock_db_session: AsyncMock
    ) -> None:
        """Should return empty list when no workflows exist."""
        with patch("app.application.services.workflow_query_service.WorkflowRepository") as mock_repo_class:
            mock_repo = AsyncMock()
            mock_repo.get_all.return_value = []
            mock_repo.count.return_value = 0
            mock_repo_class.return_value = mock_repo

            response = await client.get("/api/v1/workflows/")

        assert response.status_code == 200
        data = response.json()
        assert data["workflows"] == []
        assert data["total"] == 0

    @pytest.mark.asyncio
    async def test_list_workflows_pagination(
        self, client: AsyncClient, mock_db_session: AsyncMock
    ) -> None:
        """Should support pagination parameters."""
        mock_workflow = MagicMock()
        mock_workflow.id = 3
        mock_workflow.github_id = 12347
        mock_workflow.name = "Test"
        mock_workflow.path = ".github/workflows/test.yml"
        mock_workflow.state = "active"
        mock_workflow.repo_id = 1

        with patch("app.application.services.workflow_query_service.WorkflowRepository") as mock_repo_class:
            mock_repo = AsyncMock()
            mock_repo.get_all.return_value = [mock_workflow]
            mock_repo.count.return_value = 10
            mock_repo_class.return_value = mock_repo

            response = await client.get("/api/v1/workflows/?limit=1&offset=2")

        assert response.status_code == 200
        mock_repo.get_all.assert_called_once_with(limit=1, offset=2)


class TestGetWorkflow:
    """Tests for GET /api/v1/workflows/{workflow_id} endpoint."""

    @pytest.mark.asyncio
    async def test_get_workflow_success(
        self, client: AsyncClient, mock_db_session: AsyncMock
    ) -> None:
        """Should return workflow details when workflow exists."""
        mock_workflow = MagicMock()
        mock_workflow.id = 1
        mock_workflow.github_id = 12345
        mock_workflow.name = "CI"
        mock_workflow.path = ".github/workflows/ci.yml"
        mock_workflow.state = "active"
        mock_workflow.repo_id = 1

        with patch("app.application.services.workflow_query_service.WorkflowRepository") as mock_repo_class:
            mock_repo = AsyncMock()
            mock_repo.get_by_id.return_value = mock_workflow
            mock_repo_class.return_value = mock_repo

            response = await client.get("/api/v1/workflows/1")

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == 1
        assert data["name"] == "CI"
        assert data["state"] == "active"

    @pytest.mark.asyncio
    async def test_get_workflow_not_found(
        self, client: AsyncClient, mock_db_session: AsyncMock
    ) -> None:
        """Should return 404 when workflow does not exist."""
        with patch("app.application.services.workflow_query_service.WorkflowRepository") as mock_repo_class:
            mock_repo = AsyncMock()
            mock_repo.get_by_id.return_value = None
            mock_repo_class.return_value = mock_repo

            response = await client.get("/api/v1/workflows/999")

        assert response.status_code == 404
        data = response.json()
        assert "not found" in data["detail"].lower()

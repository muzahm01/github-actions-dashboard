"""Tests for search endpoints."""
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from httpx import AsyncClient


class TestSemanticSearch:
    """Tests for POST /api/v1/search/semantic endpoint."""

    @pytest.mark.asyncio
    async def test_semantic_search_returns_results(
        self, client: AsyncClient, mock_db_session: AsyncMock
    ) -> None:
        """Should return similar logs based on embedding similarity."""
        mock_log = MagicMock()
        mock_log.id = 1
        mock_log.job_id = 100
        mock_log.category = "test_failure"
        mock_log.log_content = "Error: test failed"

        with (
            patch("app.api.v1.search.EmbeddingClient") as mock_client_class,
            patch("app.api.v1.search.LogRepository") as mock_repo_class,
        ):
            mock_client = AsyncMock()
            mock_client.generate_embedding.return_value = [0.1] * 1536
            mock_client_class.return_value = mock_client

            mock_repo = AsyncMock()
            mock_repo.find_similar_by_embedding.return_value = [(mock_log, 0.85)]
            mock_repo_class.return_value = mock_repo

            response = await client.post(
                "/api/v1/search/semantic",
                json={"query": "test failure", "limit": 5},
            )

        assert response.status_code == 200
        data = response.json()
        assert data["query"] == "test failure"
        assert len(data["results"]) == 1
        assert data["results"][0]["log_id"] == 1
        assert data["results"][0]["similarity_score"] == 0.85
        assert data["total"] == 1

    @pytest.mark.asyncio
    async def test_semantic_search_handles_embedding_error(
        self, client: AsyncClient, mock_db_session: AsyncMock
    ) -> None:
        """Should return error message when embedding generation fails."""
        with patch("app.api.v1.search.EmbeddingClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.generate_embedding.side_effect = Exception("API error")
            mock_client_class.return_value = mock_client

            response = await client.post(
                "/api/v1/search/semantic",
                json={"query": "test failure"},
            )

        assert response.status_code == 200
        data = response.json()
        assert data["results"] == []
        assert "error" in data
        assert "Failed to generate embedding" in data["error"]


class TestTextSearch:
    """Tests for POST /api/v1/search/text endpoint."""

    @pytest.mark.asyncio
    async def test_text_search_returns_results(
        self, client: AsyncClient, mock_db_session: AsyncMock
    ) -> None:
        """Should return logs matching the text query."""
        mock_log = MagicMock()
        mock_log.id = 1
        mock_log.job_id = 100
        mock_log.category = "build_failure"
        mock_log.log_content = "npm ERR! Build failed"

        with patch("app.api.v1.search.LogRepository") as mock_repo_class:
            mock_repo = AsyncMock()
            mock_repo.search_by_content.return_value = [mock_log]
            mock_repo_class.return_value = mock_repo

            response = await client.post(
                "/api/v1/search/text",
                json={"query": "npm ERR", "limit": 10},
            )

        assert response.status_code == 200
        data = response.json()
        assert data["query"] == "npm ERR"
        assert len(data["results"]) == 1
        assert data["results"][0]["log_id"] == 1
        assert data["total"] == 1

    @pytest.mark.asyncio
    async def test_text_search_returns_empty_for_no_match(
        self, client: AsyncClient, mock_db_session: AsyncMock
    ) -> None:
        """Should return empty results when no logs match."""
        with patch("app.api.v1.search.LogRepository") as mock_repo_class:
            mock_repo = AsyncMock()
            mock_repo.search_by_content.return_value = []
            mock_repo_class.return_value = mock_repo

            response = await client.post(
                "/api/v1/search/text",
                json={"query": "nonexistent error"},
            )

        assert response.status_code == 200
        data = response.json()
        assert data["results"] == []
        assert data["total"] == 0


class TestSearchLogs:
    """Tests for GET /api/v1/search/logs endpoint."""

    @pytest.mark.asyncio
    async def test_search_logs_with_query(
        self, client: AsyncClient, mock_db_session: AsyncMock
    ) -> None:
        """Should search logs by content query."""
        mock_log = MagicMock()
        mock_log.id = 1
        mock_log.job_id = 100
        mock_log.category = "test_failure"
        mock_log.error_content = "AssertionError"
        mock_log.log_size_bytes = 1024

        with patch("app.api.v1.search.LogRepository") as mock_repo_class:
            mock_repo = AsyncMock()
            mock_repo.search_by_content.return_value = [mock_log]
            mock_repo_class.return_value = mock_repo

            response = await client.get(
                "/api/v1/search/logs",
                params={"query": "assertion"},
            )

        assert response.status_code == 200
        data = response.json()
        assert len(data["logs"]) == 1
        assert data["logs"][0]["id"] == 1
        assert data["logs"][0]["has_error"] is True

    @pytest.mark.asyncio
    async def test_search_logs_with_category(
        self, client: AsyncClient, mock_db_session: AsyncMock
    ) -> None:
        """Should filter logs by category."""
        mock_log = MagicMock()
        mock_log.id = 2
        mock_log.job_id = 200
        mock_log.category = "build_failure"
        mock_log.error_content = None
        mock_log.log_size_bytes = 2048

        with patch("app.api.v1.search.LogRepository") as mock_repo_class:
            mock_repo = AsyncMock()
            mock_repo.get_by_category.return_value = [mock_log]
            mock_repo_class.return_value = mock_repo

            response = await client.get(
                "/api/v1/search/logs",
                params={"category": "build_failure"},
            )

        assert response.status_code == 200
        data = response.json()
        assert len(data["logs"]) == 1
        assert data["logs"][0]["category"] == "build_failure"

    @pytest.mark.asyncio
    async def test_search_logs_default_returns_errors(
        self, client: AsyncClient, mock_db_session: AsyncMock
    ) -> None:
        """Should return logs with errors by default."""
        mock_log = MagicMock()
        mock_log.id = 3
        mock_log.job_id = 300
        mock_log.category = "dependency_failure"
        mock_log.error_content = "Package not found"
        mock_log.log_size_bytes = 512

        with patch("app.api.v1.search.LogRepository") as mock_repo_class:
            mock_repo = AsyncMock()
            mock_repo.get_logs_with_errors.return_value = [mock_log]
            mock_repo_class.return_value = mock_repo

            response = await client.get("/api/v1/search/logs")

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        mock_repo.get_logs_with_errors.assert_called_once()

    @pytest.mark.asyncio
    async def test_search_logs_pagination(
        self, client: AsyncClient, mock_db_session: AsyncMock
    ) -> None:
        """Should respect limit and offset parameters."""
        with patch("app.api.v1.search.LogRepository") as mock_repo_class:
            mock_repo = AsyncMock()
            mock_repo.get_logs_with_errors.return_value = []
            mock_repo_class.return_value = mock_repo

            response = await client.get(
                "/api/v1/search/logs",
                params={"limit": 50, "offset": 10},
            )

        assert response.status_code == 200
        data = response.json()
        assert data["limit"] == 50
        assert data["offset"] == 10

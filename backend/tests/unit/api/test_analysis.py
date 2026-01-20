"""Tests for analysis endpoints."""
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from httpx import AsyncClient


class TestAnalyzeError:
    """Tests for POST /api/v1/analysis/analyze endpoint."""

    @pytest.mark.asyncio
    async def test_analyze_queues_task_for_new_log(
        self, client: AsyncClient, mock_db_session: AsyncMock
    ) -> None:
        """Should queue analysis task when log exists and no analysis exists."""
        mock_log = MagicMock()
        mock_log.id = 1

        with (
            patch("app.api.v1.analysis.LogRepository") as mock_log_repo_class,
            patch("app.api.v1.analysis.ErrorAnalysisRepository") as mock_analysis_repo_class,
            patch("app.api.v1.analysis.analyze_error_log") as mock_task,
        ):
            mock_log_repo = AsyncMock()
            mock_log_repo.get_by_id.return_value = mock_log
            mock_log_repo_class.return_value = mock_log_repo

            mock_analysis_repo = AsyncMock()
            mock_analysis_repo.get_by_log_id.return_value = None
            mock_analysis_repo_class.return_value = mock_analysis_repo

            response = await client.post(
                "/api/v1/analysis/analyze",
                json={"log_id": 1},
            )

        assert response.status_code == 200
        data = response.json()
        assert data["log_id"] == 1
        assert data["status"] == "pending"
        mock_task.delay.assert_called_once_with(1)

    @pytest.mark.asyncio
    async def test_analyze_returns_existing_analysis(
        self, client: AsyncClient, mock_db_session: AsyncMock
    ) -> None:
        """Should return existing analysis if one exists."""
        mock_log = MagicMock()
        mock_log.id = 1

        mock_analysis = MagicMock()
        mock_analysis.id = 10
        mock_analysis.root_cause = "Test failure"
        mock_analysis.error_summary = "Tests failed"
        mock_analysis.suggested_fixes = ["Fix the code"]
        mock_analysis.confidence_score = 0.9

        with (
            patch("app.api.v1.analysis.LogRepository") as mock_log_repo_class,
            patch("app.api.v1.analysis.ErrorAnalysisRepository") as mock_analysis_repo_class,
        ):
            mock_log_repo = AsyncMock()
            mock_log_repo.get_by_id.return_value = mock_log
            mock_log_repo_class.return_value = mock_log_repo

            mock_analysis_repo = AsyncMock()
            mock_analysis_repo.get_by_log_id.return_value = mock_analysis
            mock_analysis_repo_class.return_value = mock_analysis_repo

            response = await client.post(
                "/api/v1/analysis/analyze",
                json={"log_id": 1},
            )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "completed"
        assert data["root_cause"] == "Test failure"

    @pytest.mark.asyncio
    async def test_analyze_returns_404_for_missing_log(
        self, client: AsyncClient, mock_db_session: AsyncMock
    ) -> None:
        """Should return 404 when log doesn't exist."""
        with patch("app.api.v1.analysis.LogRepository") as mock_log_repo_class:
            mock_log_repo = AsyncMock()
            mock_log_repo.get_by_id.return_value = None
            mock_log_repo_class.return_value = mock_log_repo

            response = await client.post(
                "/api/v1/analysis/analyze",
                json={"log_id": 999},
            )

        assert response.status_code == 404


class TestGetAnalysis:
    """Tests for GET /api/v1/analysis/{analysis_id} endpoint."""

    @pytest.mark.asyncio
    async def test_get_analysis_success(
        self, client: AsyncClient, mock_db_session: AsyncMock
    ) -> None:
        """Should return analysis details."""
        mock_analysis = MagicMock()
        mock_analysis.id = 1
        mock_analysis.log_id = 10
        mock_analysis.root_cause = "Division by zero"
        mock_analysis.error_summary = "Test failed due to division by zero"
        mock_analysis.suggested_fixes = ["Add zero check"]
        mock_analysis.prevention_tips = ["Use type hints"]
        mock_analysis.confidence_score = 0.85
        mock_analysis.related_documentation = []
        mock_analysis.llm_model = "claude-sonnet-4"
        mock_analysis.analyzed_at = None

        with patch("app.api.v1.analysis.ErrorAnalysisRepository") as mock_repo_class:
            mock_repo = AsyncMock()
            mock_repo.get_by_id.return_value = mock_analysis
            mock_repo_class.return_value = mock_repo

            response = await client.get("/api/v1/analysis/1")

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == 1
        assert data["root_cause"] == "Division by zero"

    @pytest.mark.asyncio
    async def test_get_analysis_not_found(
        self, client: AsyncClient, mock_db_session: AsyncMock
    ) -> None:
        """Should return 404 when analysis doesn't exist."""
        with patch("app.api.v1.analysis.ErrorAnalysisRepository") as mock_repo_class:
            mock_repo = AsyncMock()
            mock_repo.get_by_id.return_value = None
            mock_repo_class.return_value = mock_repo

            response = await client.get("/api/v1/analysis/999")

        assert response.status_code == 404


class TestFindSimilarErrors:
    """Tests for POST /api/v1/analysis/similar endpoint."""

    @pytest.mark.asyncio
    async def test_find_similar_returns_results(
        self, client: AsyncClient, mock_db_session: AsyncMock
    ) -> None:
        """Should return similar errors when log has embedding."""
        mock_log = MagicMock()
        mock_log.id = 1
        mock_log.embedding = [0.1] * 1536

        mock_similar_log = MagicMock()
        mock_similar_log.id = 2
        mock_similar_log.category = "test_failure"

        with patch("app.api.v1.analysis.LogRepository") as mock_log_repo_class:
            mock_log_repo = AsyncMock()
            mock_log_repo.get_by_id.return_value = mock_log
            mock_log_repo.find_similar_by_embedding.return_value = [
                (mock_similar_log, 0.85)
            ]
            mock_log_repo_class.return_value = mock_log_repo

            response = await client.post(
                "/api/v1/analysis/similar",
                json={"log_id": 1, "limit": 5},
            )

        assert response.status_code == 200
        data = response.json()
        assert data["log_id"] == 1
        assert len(data["similar_errors"]) == 1
        assert data["similar_errors"][0]["similarity_score"] == 0.85

    @pytest.mark.asyncio
    async def test_find_similar_returns_empty_without_embedding(
        self, client: AsyncClient, mock_db_session: AsyncMock
    ) -> None:
        """Should return empty list when log has no embedding."""
        mock_log = MagicMock()
        mock_log.id = 1
        mock_log.embedding = None

        with patch("app.api.v1.analysis.LogRepository") as mock_log_repo_class:
            mock_log_repo = AsyncMock()
            mock_log_repo.get_by_id.return_value = mock_log
            mock_log_repo_class.return_value = mock_log_repo

            response = await client.post(
                "/api/v1/analysis/similar",
                json={"log_id": 1},
            )

        assert response.status_code == 200
        data = response.json()
        assert data["similar_errors"] == []
        assert "message" in data

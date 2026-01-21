"""Tests for dashboard API endpoints."""

from unittest.mock import MagicMock

import pytest
from httpx import AsyncClient


class TestDashboardRouter:
    """Tests for dashboard router configuration."""

    def test_router_has_stats_endpoint(self) -> None:
        """Should have stats endpoint."""
        from app.api.v1.dashboard import router

        routes = [route.path for route in router.routes]
        assert "/stats" in routes

    def test_router_has_correct_number_of_routes(self) -> None:
        """Should have expected number of routes."""
        from app.api.v1.dashboard import router

        # 1 route: stats
        assert len(router.routes) == 1


class TestGetDashboardStats:
    """Tests for get_dashboard_stats endpoint."""

    @pytest.mark.asyncio
    async def test_returns_stats(self, client: AsyncClient, mock_db_session: MagicMock) -> None:
        """Should return dashboard statistics."""
        # Mock execute to return scalars
        mock_result = MagicMock()
        mock_result.scalar.return_value = 10
        mock_db_session.execute.return_value = mock_result

        response = await client.get("/api/v1/dashboard/stats")

        assert response.status_code == 200
        data = response.json()
        assert "total_repositories" in data
        assert "active_repositories" in data
        assert "total_workflows" in data
        assert "runs_24h" in data
        assert "success_rate_24h" in data
        assert "runs_7d" in data
        assert "success_rate_7d" in data
        assert "total_analyses" in data

    @pytest.mark.asyncio
    async def test_returns_zero_when_empty(
        self, client: AsyncClient, mock_db_session: MagicMock
    ) -> None:
        """Should return zeros for empty database."""
        mock_result = MagicMock()
        mock_result.scalar.return_value = 0
        mock_db_session.execute.return_value = mock_result

        response = await client.get("/api/v1/dashboard/stats")

        assert response.status_code == 200
        data = response.json()
        # When no runs, success rate should be 100%
        assert data["success_rate_24h"] == 100.0
        assert data["success_rate_7d"] == 100.0

    @pytest.mark.asyncio
    async def test_calculates_success_rate(
        self, client: AsyncClient, mock_db_session: MagicMock
    ) -> None:
        """Should calculate success rate correctly."""
        # Create mock results that return different values for different queries
        call_count = [0]
        values = [5, 3, 10, 10, 8, 2, 20, 16, 5, None]  # Different values for each query

        def mock_scalar() -> int | None:
            result = values[call_count[0] % len(values)]
            call_count[0] += 1
            return result

        mock_result = MagicMock()
        mock_result.scalar = mock_scalar
        mock_db_session.execute.return_value = mock_result

        response = await client.get("/api/v1/dashboard/stats")

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data["success_rate_24h"], float)
        assert isinstance(data["success_rate_7d"], float)

    @pytest.mark.asyncio
    async def test_returns_none_for_no_avg_duration(
        self, client: AsyncClient, mock_db_session: MagicMock
    ) -> None:
        """Should return None for avg_duration when no successful runs."""
        mock_result = MagicMock()
        mock_result.scalar.return_value = None
        mock_db_session.execute.return_value = mock_result

        response = await client.get("/api/v1/dashboard/stats")

        assert response.status_code == 200
        data = response.json()
        assert data["avg_duration_seconds"] is None

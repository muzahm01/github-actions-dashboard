"""Tests for dashboard API endpoints."""

from app.api.v1.dashboard import router


class TestDashboardRouter:
    """Tests for dashboard router configuration."""

    def test_router_has_stats_endpoint(self) -> None:
        """Should have stats endpoint."""
        routes = [route.path for route in router.routes]
        assert "/stats" in routes

    def test_router_has_correct_number_of_routes(self) -> None:
        """Should have expected number of routes."""
        # 1 route: stats
        assert len(router.routes) == 1

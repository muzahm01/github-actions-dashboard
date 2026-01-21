"""Tests for repositories API endpoints."""

from app.api.v1.repositories import router


class TestRepositoriesRouter:
    """Tests for repositories router configuration."""

    def test_router_has_list_endpoint(self) -> None:
        """Should have list repositories endpoint."""
        routes = [route.path for route in router.routes]
        assert "/" in routes

    def test_router_has_get_endpoint(self) -> None:
        """Should have get repository endpoint."""
        routes = [route.path for route in router.routes]
        assert "/{repository_id}" in routes

    def test_router_has_activate_endpoint(self) -> None:
        """Should have activate repository endpoint."""
        routes = [route.path for route in router.routes]
        assert "/{repository_id}/activate" in routes

    def test_router_has_deactivate_endpoint(self) -> None:
        """Should have deactivate repository endpoint."""
        routes = [route.path for route in router.routes]
        assert "/{repository_id}/deactivate" in routes

    def test_router_has_correct_number_of_routes(self) -> None:
        """Should have expected number of routes."""
        # 4 routes: list, get, activate, deactivate
        assert len(router.routes) == 4

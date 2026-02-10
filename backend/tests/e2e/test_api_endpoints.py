"""End-to-end tests for API endpoints.

These tests exercise the full FastAPI stack (routing, middleware, validation)
using an ASGI test client with mocked database dependencies.
"""

from unittest.mock import AsyncMock, patch

import pytest
from httpx import AsyncClient

pytestmark = [pytest.mark.e2e, pytest.mark.unit]


# --- Public endpoints (no auth required) ---


@pytest.mark.asyncio
async def test_health_endpoint(client: AsyncClient) -> None:
    """Health endpoint returns expected response."""
    response = await client.get("/api/v1/")
    # May return 200 or 503 depending on DB/Redis checks
    assert response.status_code in (200, 503)
    data = response.json()
    assert "status" in data


@pytest.mark.asyncio
async def test_health_ready_endpoint(client: AsyncClient) -> None:
    """Health readiness endpoint returns expected response."""
    response = await client.get("/api/v1/ready")
    assert response.status_code in (200, 503)


@pytest.mark.asyncio
async def test_health_live_endpoint(client: AsyncClient) -> None:
    """Health liveness endpoint returns 200."""
    response = await client.get("/api/v1/live")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "alive"


@pytest.mark.asyncio
async def test_metrics_endpoint(client: AsyncClient) -> None:
    """Metrics endpoint returns Prometheus metrics."""
    response = await client.get("/api/v1/metrics")
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_nonexistent_endpoint_returns_404(client: AsyncClient) -> None:
    """Non-existent endpoint returns 404."""
    response = await client.get("/api/v1/nonexistent")
    assert response.status_code == 404


# --- Authenticated endpoints ---


@pytest.mark.asyncio
async def test_dashboard_stats_endpoint(client: AsyncClient, mock_db_session: AsyncMock) -> None:
    """Dashboard stats endpoint returns valid response."""
    mock_service = AsyncMock()
    mock_service.get_stats.return_value = {
        "total_repositories": 5,
        "total_workflows": 10,
        "total_runs_24h": 42,
        "success_rate": 85.0,
        "success_rate_24h": 90.0,
        "failed_runs_24h": 4,
        "avg_duration_seconds": 120.5,
    }

    with patch("app.api.v1.dashboard.DashboardService", return_value=mock_service):
        response = await client.get("/api/v1/dashboard/stats")

    assert response.status_code == 200
    data = response.json()
    assert "total_repositories" in data


@pytest.mark.asyncio
async def test_repositories_list_endpoint(
    client: AsyncClient, mock_db_session: AsyncMock
) -> None:
    """Repositories list endpoint returns array."""
    mock_service = AsyncMock()
    mock_service.list_repositories.return_value = []

    with patch(
        "app.api.v1.repositories.RepositoryQueryService", return_value=mock_service
    ):
        response = await client.get("/api/v1/repositories/")

    assert response.status_code == 200
    assert isinstance(response.json(), list)


@pytest.mark.asyncio
async def test_workflows_list_endpoint(
    client: AsyncClient, mock_db_session: AsyncMock
) -> None:
    """Workflows list endpoint returns paginated response."""
    mock_service = AsyncMock()
    mock_service.list_workflows.return_value = ([], 0)

    with patch(
        "app.api.v1.workflows.WorkflowQueryService", return_value=mock_service
    ):
        response = await client.get("/api/v1/workflows/")

    assert response.status_code == 200
    data = response.json()
    assert "workflows" in data
    assert "total" in data


@pytest.mark.asyncio
async def test_runs_list_endpoint(
    client: AsyncClient, mock_db_session: AsyncMock
) -> None:
    """Runs list endpoint returns paginated response."""
    mock_service = AsyncMock()
    mock_service.list_runs.return_value = ([], 0)

    with patch("app.api.v1.runs.WorkflowRunQueryService", return_value=mock_service):
        response = await client.get("/api/v1/runs/")

    assert response.status_code == 200
    data = response.json()
    assert "runs" in data
    assert "total" in data


# --- Trends endpoints (return mock data, no DB needed) ---


@pytest.mark.asyncio
async def test_trends_success_rate_endpoint(client: AsyncClient) -> None:
    """Trends success rate endpoint returns valid trend data."""
    response = await client.get("/api/v1/trends/success-rate?days=7&period=daily")

    assert response.status_code == 200
    data = response.json()
    assert "period" in data
    assert "points" in data
    assert "average_rate" in data
    assert "direction" in data


@pytest.mark.asyncio
async def test_trends_summary_endpoint(client: AsyncClient) -> None:
    """Trends summary endpoint returns valid summary."""
    response = await client.get("/api/v1/trends/summary")

    assert response.status_code == 200
    data = response.json()
    assert "total_runs_today" in data
    assert "success_rate_today" in data


@pytest.mark.asyncio
async def test_trends_failures_endpoint(client: AsyncClient) -> None:
    """Trends failures endpoint returns valid data."""
    response = await client.get("/api/v1/trends/failures?days=30")

    assert response.status_code == 200
    data = response.json()
    assert "total_failures" in data
    assert "unique_errors" in data

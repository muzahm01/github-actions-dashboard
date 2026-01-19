"""Tests for health endpoints."""
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_health_check(client: AsyncClient) -> None:
    """Should return healthy status."""
    response = await client.get("/health")

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"


@pytest.mark.asyncio
async def test_readiness_check(client: AsyncClient) -> None:
    """Should return ready status with dependency checks."""
    response = await client.get("/health/ready")

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ready"
    assert "checks" in data


@pytest.mark.asyncio
async def test_liveness_check(client: AsyncClient) -> None:
    """Should return alive status."""
    response = await client.get("/health/live")

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "alive"

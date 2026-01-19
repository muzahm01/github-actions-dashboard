"""Tests for analysis endpoints."""
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_analyze_error(client: AsyncClient) -> None:
    """Should accept analysis request."""
    response = await client.post(
        "/api/v1/analysis/analyze",
        json={"log_id": 1},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["log_id"] == 1
    assert "status" in data


@pytest.mark.asyncio
async def test_get_analysis(client: AsyncClient) -> None:
    """Should return analysis details."""
    response = await client.get("/api/v1/analysis/1")

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == 1


@pytest.mark.asyncio
async def test_find_similar_errors(client: AsyncClient) -> None:
    """Should return similar errors."""
    response = await client.post(
        "/api/v1/analysis/similar",
        json={"log_id": 1, "limit": 5},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["log_id"] == 1
    assert "similar_errors" in data

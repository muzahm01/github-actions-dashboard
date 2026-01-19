"""Tests for search endpoints."""
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_semantic_search(client: AsyncClient) -> None:
    """Should accept semantic search request."""
    response = await client.post(
        "/api/v1/search/semantic",
        json={"query": "connection timeout error", "limit": 10},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["query"] == "connection timeout error"
    assert "results" in data


@pytest.mark.asyncio
async def test_text_search(client: AsyncClient) -> None:
    """Should accept text search request."""
    response = await client.post(
        "/api/v1/search/text",
        json={"query": "NullPointerException", "limit": 10},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["query"] == "NullPointerException"
    assert "results" in data


@pytest.mark.asyncio
async def test_search_with_default_limit(client: AsyncClient) -> None:
    """Should use default limit when not specified."""
    response = await client.post(
        "/api/v1/search/semantic",
        json={"query": "test error"},
    )

    assert response.status_code == 200

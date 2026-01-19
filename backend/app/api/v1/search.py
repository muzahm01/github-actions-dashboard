"""Search endpoints."""
from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter()


class SearchRequest(BaseModel):
    """Request body for search."""

    query: str
    limit: int = 10


@router.post("/semantic")
async def semantic_search(request: SearchRequest) -> dict[str, str | list[dict[str, str]]]:
    """Semantic search using embeddings."""
    return {
        "query": request.query,
        "results": [],
    }


@router.post("/text")
async def text_search(request: SearchRequest) -> dict[str, str | list[dict[str, str]]]:
    """Full-text search."""
    return {
        "query": request.query,
        "results": [],
    }

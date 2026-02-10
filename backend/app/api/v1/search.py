"""Search endpoints."""

from typing import Annotated, Any

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.services.log_search_service import LogSearchService
from app.config import Settings, get_settings
from app.infrastructure.database.session import get_db

router = APIRouter()


class SearchRequest(BaseModel):
    """Request body for search."""

    query: str = Field(..., min_length=1, max_length=1000)
    limit: int = Field(default=10, ge=1, le=100)


@router.post("/semantic")
async def semantic_search(
    request: SearchRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> dict[str, Any]:
    """
    Semantic search using embeddings.

    Converts the query to an embedding and finds similar logs using vector similarity.
    """
    service = LogSearchService(db, settings)
    return await service.semantic_search(query=request.query, limit=request.limit)


@router.post("/text")
async def text_search(
    request: SearchRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> dict[str, Any]:
    """
    Full-text search in log content.

    Uses simple ILIKE pattern matching.
    """
    service = LogSearchService(db, settings)
    logs = await service.text_search(query=request.query, limit=request.limit)

    return {
        "query": request.query,
        "results": [
            {
                "log_id": log.id,
                "job_id": log.job_id,
                "category": log.category,
                "preview": (log.log_content[:200] + "...")
                if log.log_content and len(log.log_content) > 200
                else log.log_content,
            }
            for log in logs
        ],
        "total": len(logs),
    }


@router.get("/logs")
async def search_logs(
    db: Annotated[AsyncSession, Depends(get_db)],
    settings: Annotated[Settings, Depends(get_settings)],
    query: str = Query(default="", description="Search query"),
    category: str | None = Query(default=None, description="Filter by error category"),
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
) -> dict[str, Any]:
    """
    Search logs with optional filters.
    """
    service = LogSearchService(db, settings)
    logs = await service.search_logs(query=query, category=category, limit=limit)

    return {
        "logs": [
            {
                "id": log.id,
                "job_id": log.job_id,
                "category": log.category,
                "has_error": log.error_content is not None,
                "size_bytes": log.log_size_bytes,
            }
            for log in logs
        ],
        "total": len(logs),
        "limit": limit,
        "offset": offset,
    }

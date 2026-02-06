"""Search endpoints."""

import logging
from typing import Annotated

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import Settings, get_settings
from app.infrastructure.database.repositories.log_repo import LogRepository
from app.infrastructure.database.session import get_db
from app.infrastructure.external.embedding_client import EmbeddingClient

logger = logging.getLogger(__name__)
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
) -> dict:
    """
    Semantic search using embeddings.

    Converts the query to an embedding and finds similar logs using vector similarity.
    """
    # Generate embedding for the query
    embedding_client = EmbeddingClient(settings)

    try:
        query_embedding = await embedding_client.generate_embedding(request.query)
    except Exception as e:
        logger.error("Failed to generate embedding for search", exc_info=e)
        return {
            "query": request.query,
            "results": [],
            "error": "Failed to generate embedding. Please try again later.",
        }
    finally:
        await embedding_client.close()

    # Search for similar logs
    log_repo = LogRepository(db)
    similar_logs = await log_repo.find_similar_by_embedding(
        embedding=query_embedding,
        limit=request.limit,
        threshold=0.6,  # Lower threshold for search queries
    )

    return {
        "query": request.query,
        "results": [
            {
                "log_id": log.id,
                "job_id": log.job_id,
                "similarity_score": round(score, 3),
                "category": log.category,
                "preview": (log.log_content[:200] + "...")
                if log.log_content and len(log.log_content) > 200
                else log.log_content,
            }
            for log, score in similar_logs
        ],
        "total": len(similar_logs),
    }


@router.post("/text")
async def text_search(
    request: SearchRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> dict:
    """
    Full-text search in log content.

    Uses simple ILIKE pattern matching.
    """
    log_repo = LogRepository(db)
    logs = await log_repo.search_by_content(
        query=request.query,
        limit=request.limit,
    )

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
    query: str = Query(default="", description="Search query"),
    category: str | None = Query(default=None, description="Filter by error category"),
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
) -> dict:
    """
    Search logs with optional filters.
    """
    log_repo = LogRepository(db)

    if category:
        logs = await log_repo.get_by_category(category, limit=limit)
    elif query:
        logs = await log_repo.search_by_content(query, limit=limit)
    else:
        logs = await log_repo.get_logs_with_errors(limit=limit)

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

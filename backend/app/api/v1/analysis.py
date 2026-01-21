"""Error analysis endpoints."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.database.repositories.error_analysis_repo import (
    ErrorAnalysisRepository,
)
from app.infrastructure.database.repositories.log_repo import LogRepository
from app.infrastructure.database.session import get_db
from app.tasks.analysis_tasks import analyze_error_log

router = APIRouter()


class AnalysisRequest(BaseModel):
    """Request body for error analysis."""

    log_id: int


class SimilarErrorRequest(BaseModel):
    """Request body for similar error search."""

    log_id: int
    limit: int = 5


@router.post("/analyze")
async def analyze_error(
    request: AnalysisRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> dict:
    """
    Analyze error with LLM.

    Queues the analysis task and returns immediately with pending status.
    """
    log_repo = LogRepository(db)
    log = await log_repo.get_by_id(request.log_id)

    if not log:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Log with id {request.log_id} not found",
        )

    # Check if analysis already exists
    analysis_repo = ErrorAnalysisRepository(db)
    existing = await analysis_repo.get_by_log_id(request.log_id)

    if existing:
        return {
            "analysis_id": existing.id,
            "log_id": request.log_id,
            "status": "completed",
            "root_cause": existing.root_cause,
            "error_summary": existing.error_summary,
            "suggested_fixes": existing.suggested_fixes,
            "confidence_score": existing.confidence_score,
        }

    # Queue analysis task
    analyze_error_log.delay(request.log_id)

    return {
        "log_id": request.log_id,
        "status": "pending",
        "message": "Analysis queued",
    }


@router.get("/{analysis_id}")
async def get_analysis(
    analysis_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> dict:
    """Get existing analysis by ID."""
    repo = ErrorAnalysisRepository(db)
    analysis = await repo.get_by_id(analysis_id)

    if not analysis:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Analysis with id {analysis_id} not found",
        )

    return {
        "id": analysis.id,
        "log_id": analysis.log_id,
        "root_cause": analysis.root_cause,
        "error_summary": analysis.error_summary,
        "suggested_fixes": analysis.suggested_fixes,
        "prevention_tips": analysis.prevention_tips,
        "confidence_score": analysis.confidence_score,
        "related_documentation": analysis.related_documentation,
        "llm_model": analysis.llm_model,
        "analyzed_at": analysis.analyzed_at.isoformat() if analysis.analyzed_at else None,
    }


@router.post("/similar")
async def find_similar_errors(
    request: SimilarErrorRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> dict:
    """
    Find similar errors using vector similarity search.

    Requires the log to have an embedding generated.
    """
    log_repo = LogRepository(db)
    log = await log_repo.get_by_id(request.log_id)

    if not log:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Log with id {request.log_id} not found",
        )

    # Check if log has embedding
    if not log.embedding:
        return {
            "log_id": request.log_id,
            "similar_errors": [],
            "message": "Log has no embedding. Generate embedding first.",
        }

    # Find similar logs
    similar_logs = await log_repo.find_similar_by_embedding(
        embedding=log.embedding,
        limit=request.limit,
        threshold=0.7,
    )

    return {
        "log_id": request.log_id,
        "similar_errors": [
            {
                "log_id": similar_log.id,
                "similarity_score": round(score, 3),
                "category": similar_log.category,
            }
            for similar_log, score in similar_logs
            if similar_log.id != request.log_id  # Exclude the source log
        ],
    }

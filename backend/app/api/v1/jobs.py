"""Job endpoints."""

from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.database.repositories.job_repo import JobRepository
from app.infrastructure.database.repositories.log_repo import LogRepository
from app.infrastructure.database.session import get_db

router = APIRouter()


@router.get("/{job_id}")
async def get_job(
    job_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> dict[str, Any]:
    """Get job details."""
    repo = JobRepository(db)
    job = await repo.get_by_id(job_id)

    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job with id {job_id} not found",
        )

    return {
        "id": job.id,
        "github_id": job.github_id,
        "name": job.name,
        "status": job.status,
        "conclusion": job.conclusion,
        "started_at": job.started_at.isoformat() if job.started_at else None,
        "completed_at": job.completed_at.isoformat() if job.completed_at else None,
        "runner_name": job.runner_name,
        "html_url": job.html_url,
    }


@router.get("/{job_id}/logs")
async def get_job_logs(
    job_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> dict[str, Any]:
    """Get job logs."""
    job_repo = JobRepository(db)
    job = await job_repo.get_by_id(job_id)

    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job with id {job_id} not found",
        )

    log_repo = LogRepository(db)
    logs = await log_repo.get_by_job_id(job_id)

    return {
        "job_id": job_id,
        "logs": [
            {
                "id": log.id,
                "log_content": log.log_content,
                "error_content": log.error_content,
                "log_size_bytes": log.log_size_bytes,
                "category": log.category,
            }
            for log in logs
        ],
    }

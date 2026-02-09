"""Workflow run endpoints."""

from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.database.repositories.workflow_run_repo import WorkflowRunRepository
from app.infrastructure.database.session import get_db

router = APIRouter()


@router.get("/")
async def list_runs(
    db: Annotated[AsyncSession, Depends(get_db)],
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    conclusion: str | None = Query(default=None),
) -> dict[str, Any]:
    """List all workflow runs with pagination and optional filtering."""
    repo = WorkflowRunRepository(db)

    # If filtering by failure conclusion, use specialized method
    if conclusion == "failure":
        runs = await repo.get_recent_failures(limit=limit)
        total = len(runs)
    else:
        runs = await repo.get_all(limit=limit, offset=offset)
        total = await repo.count()

    return {
        "runs": [
            {
                "id": r.id,
                "github_id": r.github_id,
                "run_number": r.run_number,
                "status": r.status,
                "conclusion": r.conclusion,
                "head_branch": r.head_branch,
                "head_sha": r.head_sha,
                "event": r.event,
                "actor": r.actor,
                "html_url": r.html_url,
                "workflow_id": r.workflow_id,
            }
            for r in runs
        ],
        "total": total,
        "limit": limit,
        "offset": offset,
    }


@router.get("/failures")
async def get_recent_failures(
    db: Annotated[AsyncSession, Depends(get_db)],
    limit: int = Query(default=10, ge=1, le=50),
) -> list[dict[str, Any]]:
    """Get recent failed workflow runs."""
    repo = WorkflowRunRepository(db)
    runs = await repo.get_recent_failures(limit=limit)

    return [
        {
            "id": r.id,
            "github_id": r.github_id,
            "run_number": r.run_number,
            "status": r.status,
            "conclusion": r.conclusion,
            "head_branch": r.head_branch,
            "head_sha": r.head_sha,
            "event": r.event,
            "actor": r.actor,
            "html_url": r.html_url,
            "workflow_id": r.workflow_id,
            "run_started_at": r.run_started_at.isoformat() if r.run_started_at else None,
            "duration_seconds": r.duration_seconds,
        }
        for r in runs
    ]


@router.get("/{run_id}")
async def get_run(
    run_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> dict[str, Any]:
    """Get workflow run details with jobs."""
    repo = WorkflowRunRepository(db)
    run = await repo.get_with_jobs(run_id)

    if not run:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Workflow run with id {run_id} not found",
        )

    return {
        "id": run.id,
        "github_id": run.github_id,
        "run_number": run.run_number,
        "status": run.status,
        "conclusion": run.conclusion,
        "head_branch": run.head_branch,
        "head_sha": run.head_sha,
        "event": run.event,
        "actor": run.actor,
        "html_url": run.html_url,
        "workflow_id": run.workflow_id,
        "run_started_at": run.run_started_at.isoformat() if run.run_started_at else None,
        "duration_seconds": run.duration_seconds,
        "jobs": [
            {
                "id": j.id,
                "github_id": j.github_id,
                "name": j.name,
                "status": j.status,
                "conclusion": j.conclusion,
            }
            for j in run.jobs
        ],
    }

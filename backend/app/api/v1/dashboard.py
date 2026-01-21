"""Dashboard API endpoints."""

from datetime import UTC, datetime, timedelta
from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.database.models.error_analysis import ErrorAnalysis
from app.infrastructure.database.models.repository import Repository
from app.infrastructure.database.models.workflow import Workflow
from app.infrastructure.database.models.workflow_run import WorkflowRun
from app.infrastructure.database.session import get_db

router = APIRouter()


@router.get("/stats")
async def get_dashboard_stats(
    db: Annotated[AsyncSession, Depends(get_db)],
) -> dict:
    """Get dashboard statistics including run counts and success rates."""
    now = datetime.now(UTC)
    last_24h = now - timedelta(hours=24)
    last_7d = now - timedelta(days=7)

    # Total repositories
    repo_count_stmt = select(func.count(Repository.id))
    repo_count = (await db.execute(repo_count_stmt)).scalar() or 0

    # Active repositories
    active_repo_stmt = select(func.count(Repository.id)).where(Repository.is_active.is_(True))
    active_repo_count = (await db.execute(active_repo_stmt)).scalar() or 0

    # Total workflows
    workflow_count_stmt = select(func.count(Workflow.id))
    workflow_count = (await db.execute(workflow_count_stmt)).scalar() or 0

    # Runs in last 24 hours
    runs_24h_stmt = select(func.count(WorkflowRun.id)).where(WorkflowRun.created_at >= last_24h)
    runs_24h = (await db.execute(runs_24h_stmt)).scalar() or 0

    # Successful runs in last 24 hours
    success_24h_stmt = select(func.count(WorkflowRun.id)).where(
        WorkflowRun.created_at >= last_24h,
        WorkflowRun.conclusion == "success",
    )
    success_24h = (await db.execute(success_24h_stmt)).scalar() or 0

    # Failed runs in last 24 hours
    failed_24h_stmt = select(func.count(WorkflowRun.id)).where(
        WorkflowRun.created_at >= last_24h,
        WorkflowRun.conclusion == "failure",
    )
    failed_24h = (await db.execute(failed_24h_stmt)).scalar() or 0

    # Success rate in last 24 hours
    success_rate_24h = (success_24h / runs_24h * 100) if runs_24h > 0 else 100.0

    # Runs in last 7 days
    runs_7d_stmt = select(func.count(WorkflowRun.id)).where(WorkflowRun.created_at >= last_7d)
    runs_7d = (await db.execute(runs_7d_stmt)).scalar() or 0

    # Success rate in last 7 days
    success_7d_stmt = select(func.count(WorkflowRun.id)).where(
        WorkflowRun.created_at >= last_7d,
        WorkflowRun.conclusion == "success",
    )
    success_7d = (await db.execute(success_7d_stmt)).scalar() or 0
    success_rate_7d = (success_7d / runs_7d * 100) if runs_7d > 0 else 100.0

    # Total error analyses
    analysis_count_stmt = select(func.count(ErrorAnalysis.id))
    analysis_count = (await db.execute(analysis_count_stmt)).scalar() or 0

    # Average duration of successful runs
    avg_duration_stmt = select(func.avg(WorkflowRun.duration_seconds)).where(
        WorkflowRun.conclusion == "success",
        WorkflowRun.duration_seconds.isnot(None),
    )
    avg_duration = (await db.execute(avg_duration_stmt)).scalar()

    return {
        "total_repositories": repo_count,
        "active_repositories": active_repo_count,
        "total_workflows": workflow_count,
        "runs_24h": runs_24h,
        "success_24h": success_24h,
        "failed_24h": failed_24h,
        "success_rate_24h": round(success_rate_24h, 2),
        "runs_7d": runs_7d,
        "success_rate_7d": round(success_rate_7d, 2),
        "total_analyses": analysis_count,
        "avg_duration_seconds": round(avg_duration, 2) if avg_duration else None,
    }

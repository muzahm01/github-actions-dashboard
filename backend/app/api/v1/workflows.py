"""Workflow endpoints."""

from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.services.workflow_query_service import WorkflowQueryService
from app.infrastructure.database.session import get_db

router = APIRouter()


@router.get("/")
async def list_workflows(
    db: Annotated[AsyncSession, Depends(get_db)],
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
) -> dict[str, Any]:
    """List all workflows with pagination."""
    service = WorkflowQueryService(db)
    workflows, total = await service.list_workflows(limit=limit, offset=offset)

    return {
        "workflows": [
            {
                "id": w.id,
                "github_id": w.github_id,
                "name": w.name,
                "path": w.path,
                "state": w.state,
                "repo_id": w.repo_id,
            }
            for w in workflows
        ],
        "total": total,
        "limit": limit,
        "offset": offset,
    }


@router.get("/{workflow_id}")
async def get_workflow(
    workflow_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> dict[str, Any]:
    """Get workflow details."""
    service = WorkflowQueryService(db)
    workflow = await service.get_workflow(workflow_id)

    if not workflow:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Workflow with id {workflow_id} not found",
        )

    return {
        "id": workflow.id,
        "github_id": workflow.github_id,
        "name": workflow.name,
        "path": workflow.path,
        "state": workflow.state,
        "repo_id": workflow.repo_id,
    }

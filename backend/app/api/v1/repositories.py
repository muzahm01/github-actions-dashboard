"""Repository API endpoints."""

from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.services.repository_query_service import RepositoryQueryService
from app.infrastructure.database.session import get_db

router = APIRouter()


@router.get("/")
async def list_repositories(
    db: Annotated[AsyncSession, Depends(get_db)],
    active_only: bool = Query(default=False, description="Filter to only active repositories"),
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
) -> list[dict[str, Any]]:
    """List all repositories."""
    service = RepositoryQueryService(db)
    repositories = await service.list_repositories(
        active_only=active_only, limit=limit, offset=offset
    )
    return [await service.serialize_repository(r) for r in repositories]


@router.get("/{repository_id}")
async def get_repository(
    repository_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> dict[str, Any]:
    """Get repository details."""
    service = RepositoryQueryService(db)
    repository = await service.get_repository(repository_id)

    if not repository:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Repository with id {repository_id} not found",
        )

    return await service.serialize_repository(repository)


@router.post("/{repository_id}/activate")
async def activate_repository(
    repository_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> dict[str, Any]:
    """Activate a repository for monitoring."""
    service = RepositoryQueryService(db)
    repository = await service.activate_repository(repository_id)

    if not repository:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Repository with id {repository_id} not found",
        )

    return {"message": "Repository activated", "id": repository_id}


@router.post("/{repository_id}/deactivate")
async def deactivate_repository(
    repository_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> dict[str, Any]:
    """Deactivate a repository from monitoring."""
    service = RepositoryQueryService(db)
    repository = await service.deactivate_repository(repository_id)

    if not repository:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Repository with id {repository_id} not found",
        )

    return {"message": "Repository deactivated", "id": repository_id}

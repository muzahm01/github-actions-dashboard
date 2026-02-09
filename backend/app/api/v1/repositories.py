"""Repository API endpoints."""

from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.database.repositories.repository_repo import RepositoryRepository
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
    repo = RepositoryRepository(db)

    if active_only:
        repositories = await repo.get_active()
    else:
        repositories = await repo.get_all(limit=limit, offset=offset)

    return [
        {
            "id": r.id,
            "github_id": r.github_id,
            "name": r.name,
            "full_name": r.full_name,
            "owner": r.owner,
            "description": r.description,
            "is_active": r.is_active,
            "webhook_configured": r.webhook_configured,
            "last_synced_at": r.last_synced_at.isoformat() if r.last_synced_at else None,
            "created_at": r.created_at.isoformat() if r.created_at else None,
        }
        for r in repositories
    ]


@router.get("/{repository_id}")
async def get_repository(
    repository_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> dict[str, Any]:
    """Get repository details."""
    repo = RepositoryRepository(db)
    repository = await repo.get_by_id(repository_id)

    if not repository:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Repository with id {repository_id} not found",
        )

    return {
        "id": repository.id,
        "github_id": repository.github_id,
        "name": repository.name,
        "full_name": repository.full_name,
        "owner": repository.owner,
        "description": repository.description,
        "is_active": repository.is_active,
        "webhook_configured": repository.webhook_configured,
        "last_synced_at": repository.last_synced_at.isoformat()
        if repository.last_synced_at
        else None,
        "created_at": repository.created_at.isoformat() if repository.created_at else None,
    }


@router.post("/{repository_id}/activate")
async def activate_repository(
    repository_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> dict[str, Any]:
    """Activate a repository for monitoring."""
    repo = RepositoryRepository(db)
    repository = await repo.get_by_id(repository_id)

    if not repository:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Repository with id {repository_id} not found",
        )

    repository.is_active = True
    await repo.update(repository)

    return {"message": "Repository activated", "id": repository_id}


@router.post("/{repository_id}/deactivate")
async def deactivate_repository(
    repository_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> dict[str, Any]:
    """Deactivate a repository from monitoring."""
    repo = RepositoryRepository(db)
    repository = await repo.get_by_id(repository_id)

    if not repository:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Repository with id {repository_id} not found",
        )

    repository.is_active = False
    await repo.update(repository)

    return {"message": "Repository deactivated", "id": repository_id}

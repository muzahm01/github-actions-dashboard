"""Repository query service."""

from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.database.models.repository import Repository
from app.infrastructure.database.repositories.repository_repo import RepositoryRepository


class RepositoryQueryService:
    """Service for querying and managing GitHub repositories."""

    def __init__(self, session: AsyncSession) -> None:
        """Initialize with database session."""
        self._repo = RepositoryRepository(session)

    async def list_repositories(
        self,
        active_only: bool = False,
        limit: int = 50,
        offset: int = 0,
    ) -> list[Repository]:
        """List repositories, optionally filtering to active only."""
        if active_only:
            return await self._repo.get_active()
        return await self._repo.get_all(limit=limit, offset=offset)

    async def get_repository(self, repository_id: int) -> Repository | None:
        """Get a repository by ID."""
        return await self._repo.get_by_id(repository_id)

    async def activate_repository(self, repository_id: int) -> Repository | None:
        """Activate a repository for monitoring."""
        repository = await self._repo.get_by_id(repository_id)
        if not repository:
            return None
        repository.is_active = True
        return await self._repo.update(repository)

    async def deactivate_repository(self, repository_id: int) -> Repository | None:
        """Deactivate a repository from monitoring."""
        repository = await self._repo.get_by_id(repository_id)
        if not repository:
            return None
        repository.is_active = False
        return await self._repo.update(repository)

    async def serialize_repository(self, r: Repository) -> dict[str, Any]:
        """Serialize a repository to a dict."""
        return {
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

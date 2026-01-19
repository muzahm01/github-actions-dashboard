"""Repository for GitHub repositories."""
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.database.models.repository import Repository
from app.infrastructure.database.repositories.base import BaseRepository


class RepositoryRepository(BaseRepository[Repository]):
    """Repository for managing GitHub repository entities."""

    def __init__(self, session: AsyncSession) -> None:
        """Initialize with session."""
        super().__init__(session, Repository)

    async def get_by_github_id(self, github_id: int) -> Repository | None:
        """Get repository by GitHub ID."""
        stmt = select(Repository).where(Repository.github_id == github_id)
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_full_name(self, full_name: str) -> Repository | None:
        """Get repository by full name (owner/repo)."""
        stmt = select(Repository).where(Repository.full_name == full_name)
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_active(self) -> list[Repository]:
        """Get all active repositories."""
        stmt = select(Repository).where(Repository.is_active.is_(True))
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def get_by_owner(self, owner: str) -> list[Repository]:
        """Get all repositories for an owner/organization."""
        stmt = select(Repository).where(Repository.owner == owner)
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def upsert_by_github_id(self, repo_data: dict) -> Repository:
        """Insert or update repository by GitHub ID."""
        github_id = repo_data["github_id"]
        existing = await self.get_by_github_id(github_id)

        if existing:
            for key, value in repo_data.items():
                if hasattr(existing, key):
                    setattr(existing, key, value)
            return await self.update(existing)
        else:
            repo = Repository(**repo_data)
            return await self.create(repo)

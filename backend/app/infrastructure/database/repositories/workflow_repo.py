"""Repository for workflows."""

from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.infrastructure.database.models.workflow import Workflow
from app.infrastructure.database.repositories.base import BaseRepository


class WorkflowRepository(BaseRepository[Workflow]):
    """Repository for managing workflow entities."""

    def __init__(self, session: AsyncSession) -> None:
        """Initialize with session."""
        super().__init__(session, Workflow)

    async def get_by_github_id(self, github_id: int) -> Workflow | None:
        """Get workflow by GitHub ID."""
        stmt = select(Workflow).where(Workflow.github_id == github_id)
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_repo_id(
        self, repo_id: int, limit: int = 100, offset: int = 0
    ) -> list[Workflow]:
        """Get all workflows for a repository."""
        stmt = (
            select(Workflow)
            .where(Workflow.repo_id == repo_id)
            .options(selectinload(Workflow.workflow_runs))
            .limit(limit)
            .offset(offset)
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def get_with_runs(self, workflow_id: int) -> Workflow | None:
        """Get workflow with its runs eagerly loaded."""
        stmt = (
            select(Workflow)
            .where(Workflow.id == workflow_id)
            .options(selectinload(Workflow.workflow_runs))
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def upsert_by_github_id(self, workflow_data: dict[str, Any]) -> Workflow:
        """Insert or update workflow by GitHub ID."""
        github_id = workflow_data["github_id"]
        existing = await self.get_by_github_id(github_id)

        if existing:
            for key, value in workflow_data.items():
                if hasattr(existing, key):
                    setattr(existing, key, value)
            return await self.update(existing)
        else:
            workflow = Workflow(**workflow_data)
            return await self.create(workflow)

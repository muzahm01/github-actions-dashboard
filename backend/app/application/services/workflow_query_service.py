"""Workflow query service."""

from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.database.models.workflow import Workflow
from app.infrastructure.database.repositories.workflow_repo import WorkflowRepository


class WorkflowQueryService:
    """Service for querying workflows."""

    def __init__(self, session: AsyncSession) -> None:
        """Initialize with database session."""
        self._repo = WorkflowRepository(session)

    async def list_workflows(
        self, limit: int = 20, offset: int = 0
    ) -> tuple[list[Workflow], int]:
        """List workflows with pagination. Returns (workflows, total_count)."""
        workflows = await self._repo.get_all(limit=limit, offset=offset)
        total = await self._repo.count()
        return workflows, total

    async def get_workflow(self, workflow_id: int) -> Workflow | None:
        """Get a workflow by ID."""
        return await self._repo.get_by_id(workflow_id)

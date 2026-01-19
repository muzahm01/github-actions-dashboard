"""Base repository with common CRUD operations."""
from typing import Generic, TypeVar

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.database.models.base import Base

ModelT = TypeVar("ModelT", bound=Base)


class BaseRepository(Generic[ModelT]):
    """Base repository with common database operations."""

    def __init__(self, session: AsyncSession, model: type[ModelT]) -> None:
        """Initialize repository with session and model class."""
        self._session = session
        self._model = model

    async def get_by_id(self, id: int) -> ModelT | None:
        """Get entity by primary key."""
        return await self._session.get(self._model, id)

    async def get_all(self, limit: int = 100, offset: int = 0) -> list[ModelT]:
        """Get all entities with pagination."""
        stmt = select(self._model).limit(limit).offset(offset)
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def create(self, entity: ModelT) -> ModelT:
        """Create a new entity."""
        self._session.add(entity)
        await self._session.flush()
        await self._session.refresh(entity)
        return entity

    async def update(self, entity: ModelT) -> ModelT:
        """Update an existing entity."""
        await self._session.flush()
        await self._session.refresh(entity)
        return entity

    async def delete(self, entity: ModelT) -> None:
        """Delete an entity."""
        await self._session.delete(entity)
        await self._session.flush()

    async def delete_by_id(self, id: int) -> bool:
        """Delete entity by ID. Returns True if deleted."""
        entity = await self.get_by_id(id)
        if entity:
            await self.delete(entity)
            return True
        return False

    async def count(self) -> int:
        """Count all entities."""
        from sqlalchemy import func

        stmt = select(func.count()).select_from(self._model)
        result = await self._session.execute(stmt)
        return result.scalar() or 0

    async def exists(self, id: int) -> bool:
        """Check if entity exists."""
        entity = await self.get_by_id(id)
        return entity is not None

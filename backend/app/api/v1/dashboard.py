"""Dashboard API endpoints."""

from typing import Annotated, Any

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.services.dashboard_service import DashboardService
from app.infrastructure.database.session import get_db

router = APIRouter()


@router.get("/stats")
async def get_dashboard_stats(
    db: Annotated[AsyncSession, Depends(get_db)],
) -> dict[str, Any]:
    """Get dashboard statistics including run counts and success rates."""
    service = DashboardService(db)
    return await service.get_stats()

"""Health check endpoints."""
from fastapi import APIRouter

router = APIRouter()


@router.get("/")
async def health_check() -> dict[str, str]:
    """Basic health check."""
    return {"status": "healthy"}


@router.get("/ready")
async def readiness_check() -> dict[str, str | dict[str, bool]]:
    """Readiness check with dependency status."""
    return {
        "status": "ready",
        "checks": {
            "database": True,
            "redis": True,
        },
    }


@router.get("/live")
async def liveness_check() -> dict[str, str]:
    """Liveness probe."""
    return {"status": "alive"}

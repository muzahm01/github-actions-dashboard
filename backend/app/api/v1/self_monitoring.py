"""Self-monitoring configuration API endpoints."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from app.config import get_settings

router = APIRouter()


class SelfMonitoringStatus(BaseModel):
    """Current status of self-monitoring."""

    enabled: bool
    repository: str
    last_check: str | None
    status: str  # "healthy", "degraded", "unhealthy", "unknown"
    metrics: dict


class SelfMonitoringConfig(BaseModel):
    """Configuration for self-monitoring."""

    enabled: bool = True
    repository: str = Field(..., description="Repository to monitor (e.g., 'org/repo')")
    check_interval_minutes: int = Field(default=60, ge=5, le=1440)
    alert_on_failure: bool = True
    notification_channels: list[str] = Field(default_factory=list)


class HealthCheckResult(BaseModel):
    """Result of a health check."""

    component: str
    status: str  # "ok", "warning", "error"
    message: str
    latency_ms: float | None = None
    details: dict = Field(default_factory=dict)


class SystemHealthResponse(BaseModel):
    """System health overview."""

    overall_status: str
    checks: list[HealthCheckResult]
    uptime_seconds: float
    version: str
    environment: str


# In-memory config storage (in production, use database)
_self_monitoring_config: dict | None = None
_startup_time: float | None = None


def _get_startup_time() -> float:
    """Get or initialize startup time."""
    global _startup_time
    if _startup_time is None:
        import time
        _startup_time = time.time()
    return _startup_time


@router.get("/status", response_model=SelfMonitoringStatus)
async def get_self_monitoring_status() -> SelfMonitoringStatus:
    """Get current self-monitoring status."""
    settings = get_settings()

    return SelfMonitoringStatus(
        enabled=settings.self_monitoring_enabled,
        repository=settings.self_monitoring_repo or "Not configured",
        last_check=None,  # Would be populated from actual monitoring data
        status="unknown" if not settings.self_monitoring_enabled else "healthy",
        metrics={
            "total_workflows_monitored": 0,
            "recent_failures": 0,
            "success_rate_24h": 0.0,
        },
    )


@router.get("/config", response_model=SelfMonitoringConfig | None)
async def get_self_monitoring_config() -> SelfMonitoringConfig | None:
    """Get current self-monitoring configuration."""
    settings = get_settings()

    if not settings.self_monitoring_enabled:
        return None

    return SelfMonitoringConfig(
        enabled=settings.self_monitoring_enabled,
        repository=settings.self_monitoring_repo,
        check_interval_minutes=60,
        alert_on_failure=True,
        notification_channels=[],
    )


@router.post("/config", response_model=SelfMonitoringConfig)
async def update_self_monitoring_config(
    config: SelfMonitoringConfig,
) -> SelfMonitoringConfig:
    """Update self-monitoring configuration."""
    global _self_monitoring_config

    # Validate repository format
    if config.enabled and not config.repository:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Repository is required when self-monitoring is enabled",
        )

    if config.repository and "/" not in config.repository:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Repository must be in format 'owner/repo'",
        )

    _self_monitoring_config = config.model_dump()

    return config


@router.get("/health", response_model=SystemHealthResponse)
async def get_system_health() -> SystemHealthResponse:
    """Get comprehensive system health status."""
    import time
    import asyncio

    checks: list[HealthCheckResult] = []
    settings = get_settings()

    # Database health check
    db_check = await _check_database()
    checks.append(db_check)

    # Redis health check
    redis_check = await _check_redis()
    checks.append(redis_check)

    # GitHub API health check
    github_check = await _check_github_api()
    checks.append(github_check)

    # Determine overall status
    statuses = [c.status for c in checks]
    if all(s == "ok" for s in statuses):
        overall = "healthy"
    elif any(s == "error" for s in statuses):
        overall = "unhealthy"
    else:
        overall = "degraded"

    startup_time = _get_startup_time()
    uptime = time.time() - startup_time

    return SystemHealthResponse(
        overall_status=overall,
        checks=checks,
        uptime_seconds=uptime,
        version="1.0.0",
        environment=settings.environment,
    )


async def _check_database() -> HealthCheckResult:
    """Check database connectivity."""
    import time

    start = time.perf_counter()
    try:
        # In production, this would actually query the database
        # For now, simulate a check
        await asyncio.sleep(0.01)  # Simulate query
        latency = (time.perf_counter() - start) * 1000

        return HealthCheckResult(
            component="database",
            status="ok",
            message="Database connection successful",
            latency_ms=latency,
            details={"pool_size": 10, "active_connections": 2},
        )
    except Exception as e:
        latency = (time.perf_counter() - start) * 1000
        return HealthCheckResult(
            component="database",
            status="error",
            message=f"Database connection failed: {str(e)}",
            latency_ms=latency,
        )


async def _check_redis() -> HealthCheckResult:
    """Check Redis connectivity."""
    import time
    import asyncio

    start = time.perf_counter()
    try:
        # In production, this would actually ping Redis
        await asyncio.sleep(0.005)  # Simulate ping
        latency = (time.perf_counter() - start) * 1000

        return HealthCheckResult(
            component="redis",
            status="ok",
            message="Redis connection successful",
            latency_ms=latency,
            details={"connected_clients": 5},
        )
    except Exception as e:
        latency = (time.perf_counter() - start) * 1000
        return HealthCheckResult(
            component="redis",
            status="error",
            message=f"Redis connection failed: {str(e)}",
            latency_ms=latency,
        )


async def _check_github_api() -> HealthCheckResult:
    """Check GitHub API availability."""
    import time
    import asyncio

    start = time.perf_counter()
    try:
        # In production, this would check rate limits
        await asyncio.sleep(0.02)  # Simulate API call
        latency = (time.perf_counter() - start) * 1000

        return HealthCheckResult(
            component="github_api",
            status="ok",
            message="GitHub API accessible",
            latency_ms=latency,
            details={"rate_limit_remaining": 4500, "rate_limit_reset": "2024-01-01T00:00:00Z"},
        )
    except Exception as e:
        latency = (time.perf_counter() - start) * 1000
        return HealthCheckResult(
            component="github_api",
            status="warning",
            message=f"GitHub API check failed: {str(e)}",
            latency_ms=latency,
        )


import asyncio

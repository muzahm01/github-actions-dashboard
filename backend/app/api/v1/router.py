"""API v1 router aggregator."""

from fastapi import APIRouter

from app.api.v1 import (
    analysis,
    dashboard,
    health,
    jobs,
    metrics,
    notifications,
    prompts,
    repositories,
    runs,
    search,
    self_monitoring,
    trends,
    webhooks,
    websocket,
    workflows,
)
from app.api.v1.security import require_api_key

api_router = APIRouter()

# Public endpoints — no authentication required
api_router.include_router(health.router, tags=["Health"])
api_router.include_router(metrics.router, tags=["Metrics"])
api_router.include_router(websocket.router, tags=["WebSocket"])

# Webhook endpoint — uses its own HMAC-based authentication
api_router.include_router(webhooks.router, prefix="/webhooks", tags=["Webhooks"])

# Authenticated endpoints — require API key
_auth = [require_api_key]
api_router.include_router(
    dashboard.router, prefix="/dashboard", tags=["Dashboard"], dependencies=_auth
)
api_router.include_router(
    repositories.router, prefix="/repositories", tags=["Repositories"], dependencies=_auth
)
api_router.include_router(
    workflows.router, prefix="/workflows", tags=["Workflows"], dependencies=_auth
)
api_router.include_router(runs.router, prefix="/runs", tags=["Runs"], dependencies=_auth)
api_router.include_router(jobs.router, prefix="/jobs", tags=["Jobs"], dependencies=_auth)
api_router.include_router(
    analysis.router, prefix="/analysis", tags=["Analysis"], dependencies=_auth
)
api_router.include_router(search.router, prefix="/search", tags=["Search"], dependencies=_auth)
api_router.include_router(
    notifications.router, prefix="/notifications", tags=["Notifications"], dependencies=_auth
)
api_router.include_router(trends.router, prefix="/trends", tags=["Trends"], dependencies=_auth)
api_router.include_router(prompts.router, prefix="/prompts", tags=["Prompts"], dependencies=_auth)
api_router.include_router(
    self_monitoring.router,
    prefix="/self-monitoring",
    tags=["Self-Monitoring"],
    dependencies=_auth,
)

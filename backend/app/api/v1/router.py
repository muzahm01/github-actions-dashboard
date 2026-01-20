"""API v1 router aggregator."""
from fastapi import APIRouter

from app.api.v1 import analysis, health, jobs, metrics, runs, search, webhooks, workflows

api_router = APIRouter()

api_router.include_router(health.router, tags=["Health"])
api_router.include_router(metrics.router, tags=["Metrics"])
api_router.include_router(webhooks.router, prefix="/webhooks", tags=["Webhooks"])
api_router.include_router(workflows.router, prefix="/workflows", tags=["Workflows"])
api_router.include_router(runs.router, prefix="/runs", tags=["Runs"])
api_router.include_router(jobs.router, prefix="/jobs", tags=["Jobs"])
api_router.include_router(analysis.router, prefix="/analysis", tags=["Analysis"])
api_router.include_router(search.router, prefix="/search", tags=["Search"])

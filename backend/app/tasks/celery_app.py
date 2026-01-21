"""Celery application configuration."""

from celery import Celery

from app.config import get_settings

settings = get_settings()

celery_app = Celery(
    "github_actions_dashboard",
    broker=str(settings.redis_url),
    backend=str(settings.redis_url),
    include=[
        "app.tasks.workflow_tasks",
        "app.tasks.analysis_tasks",
        "app.tasks.webhook_tasks",
    ],
)

# Celery configuration
celery_app.conf.update(
    # Task settings
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    # Task execution settings
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    # Worker settings
    worker_prefetch_multiplier=1,
    worker_concurrency=4,
    # Result backend settings
    result_expires=3600,  # 1 hour
    # Beat scheduler
    beat_schedule={
        "sync-workflows-every-5-minutes": {
            "task": "app.tasks.workflow_tasks.sync_all_workflows",
            "schedule": 300.0,  # 5 minutes
        },
        "cleanup-old-data-daily": {
            "task": "app.tasks.workflow_tasks.cleanup_old_data",
            "schedule": 86400.0,  # 24 hours
        },
    },
)

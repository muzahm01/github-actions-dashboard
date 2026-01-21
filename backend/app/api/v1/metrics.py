"""Prometheus metrics endpoint."""

import logging
import time
from collections.abc import Callable
from functools import wraps
from typing import Any

from fastapi import APIRouter, Request, Response
from prometheus_client import (
    CONTENT_TYPE_LATEST,
    Counter,
    Gauge,
    Histogram,
    generate_latest,
)

logger = logging.getLogger(__name__)
router = APIRouter()

# Request metrics
REQUEST_COUNT = Counter(
    "http_requests_total",
    "Total HTTP requests",
    ["method", "endpoint", "status_code"],
)

REQUEST_LATENCY = Histogram(
    "http_request_duration_seconds",
    "HTTP request latency in seconds",
    ["method", "endpoint"],
    buckets=[0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0],
)

# Webhook metrics
WEBHOOK_RECEIVED = Counter(
    "webhook_received_total",
    "Total webhooks received",
    ["event_type", "status"],
)

WEBHOOK_PROCESSING_TIME = Histogram(
    "webhook_processing_seconds",
    "Webhook processing time in seconds",
    ["event_type"],
    buckets=[0.1, 0.5, 1.0, 2.5, 5.0, 10.0, 30.0],
)

# Workflow metrics
WORKFLOW_RUNS = Counter(
    "workflow_runs_total",
    "Total workflow runs processed",
    ["repository", "workflow", "conclusion"],
)

FAILED_JOBS = Counter(
    "failed_jobs_total",
    "Total failed jobs",
    ["repository", "job_name"],
)

# LLM metrics
LLM_REQUESTS = Counter(
    "llm_requests_total",
    "Total LLM API requests",
    ["provider", "operation", "status"],
)

LLM_TOKENS_USED = Counter(
    "llm_tokens_total",
    "Total LLM tokens used",
    ["provider", "operation"],
)

LLM_LATENCY = Histogram(
    "llm_request_duration_seconds",
    "LLM API request latency",
    ["provider", "operation"],
    buckets=[0.5, 1.0, 2.5, 5.0, 10.0, 30.0, 60.0],
)

# Database metrics
DB_CONNECTIONS_ACTIVE = Gauge(
    "db_connections_active",
    "Active database connections",
)

DB_QUERY_LATENCY = Histogram(
    "db_query_duration_seconds",
    "Database query latency",
    ["operation"],
    buckets=[0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0],
)

# Task queue metrics
CELERY_TASKS_QUEUED = Counter(
    "celery_tasks_queued_total",
    "Total tasks queued",
    ["task_name"],
)

CELERY_TASKS_COMPLETED = Counter(
    "celery_tasks_completed_total",
    "Total tasks completed",
    ["task_name", "status"],
)

CELERY_TASK_DURATION = Histogram(
    "celery_task_duration_seconds",
    "Celery task duration",
    ["task_name"],
    buckets=[0.1, 0.5, 1.0, 5.0, 10.0, 30.0, 60.0, 300.0],
)

# System metrics
REPOSITORIES_MONITORED = Gauge(
    "repositories_monitored_total",
    "Total repositories being monitored",
)

LOGS_STORED = Gauge(
    "logs_stored_total",
    "Total error logs stored",
)

EMBEDDINGS_GENERATED = Gauge(
    "embeddings_generated_total",
    "Total embeddings generated",
)


@router.get("/metrics")
async def metrics() -> Response:
    """Expose Prometheus metrics."""
    return Response(
        content=generate_latest(),
        media_type=CONTENT_TYPE_LATEST,
    )


def track_request_metrics(func: Callable[..., Any]) -> Callable[..., Any]:
    """Decorator to track request metrics."""

    @wraps(func)
    async def wrapper(request: Request, *args: Any, **kwargs: Any) -> Any:
        method = request.method
        endpoint = request.url.path

        start_time = time.perf_counter()
        try:
            response = await func(request, *args, **kwargs)
            status_code = getattr(response, "status_code", 200)
            REQUEST_COUNT.labels(method=method, endpoint=endpoint, status_code=status_code).inc()
            return response
        except Exception:
            REQUEST_COUNT.labels(method=method, endpoint=endpoint, status_code=500).inc()
            raise
        finally:
            duration = time.perf_counter() - start_time
            REQUEST_LATENCY.labels(method=method, endpoint=endpoint).observe(duration)

    return wrapper


def record_webhook_received(event_type: str, status: str) -> None:
    """Record a webhook received event."""
    WEBHOOK_RECEIVED.labels(event_type=event_type, status=status).inc()


def record_webhook_processing_time(event_type: str, duration: float) -> None:
    """Record webhook processing time."""
    WEBHOOK_PROCESSING_TIME.labels(event_type=event_type).observe(duration)


def record_workflow_run(repository: str, workflow: str, conclusion: str) -> None:
    """Record a workflow run."""
    WORKFLOW_RUNS.labels(repository=repository, workflow=workflow, conclusion=conclusion).inc()


def record_failed_job(repository: str, job_name: str) -> None:
    """Record a failed job."""
    FAILED_JOBS.labels(repository=repository, job_name=job_name).inc()


def record_llm_request(
    provider: str, operation: str, status: str, tokens: int = 0, duration: float = 0
) -> None:
    """Record an LLM API request."""
    LLM_REQUESTS.labels(provider=provider, operation=operation, status=status).inc()
    if tokens > 0:
        LLM_TOKENS_USED.labels(provider=provider, operation=operation).inc(tokens)
    if duration > 0:
        LLM_LATENCY.labels(provider=provider, operation=operation).observe(duration)


def record_celery_task(task_name: str, status: str, duration: float = 0) -> None:
    """Record a Celery task completion."""
    CELERY_TASKS_COMPLETED.labels(task_name=task_name, status=status).inc()
    if duration > 0:
        CELERY_TASK_DURATION.labels(task_name=task_name).observe(duration)


def set_repositories_count(count: int) -> None:
    """Set the number of monitored repositories."""
    REPOSITORIES_MONITORED.set(count)


def set_logs_count(count: int) -> None:
    """Set the number of stored logs."""
    LOGS_STORED.set(count)


def set_embeddings_count(count: int) -> None:
    """Set the number of generated embeddings."""
    EMBEDDINGS_GENERATED.set(count)

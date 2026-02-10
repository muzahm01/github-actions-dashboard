"""Celery tasks for webhook event processing."""

import asyncio
import logging
from collections.abc import Coroutine
from dataclasses import dataclass
from typing import Any, TypeVar

from celery import Task

from app.config import get_settings
from app.tasks.celery_app import celery_app
from app.tasks.workflow_tasks import process_workflow_run

logger = logging.getLogger(__name__)
settings = get_settings()


_T = TypeVar("_T")


def run_async(coro: Coroutine[Any, Any, _T]) -> _T:
    """Helper to run async code in sync Celery tasks."""
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


@dataclass
class ProcessedWebhookResult:
    """Result of webhook event processing."""

    status: str  # "processed", "skipped", "error"
    event_type: str
    action: str
    delivery_id: str
    reason: str | None = None
    triggered_tasks: list[str] | None = None


# Supported event types and actions
SUPPORTED_EVENTS = {
    "workflow_run": {"completed", "requested"},
    "workflow_job": {"completed", "in_progress", "queued"},
}


@celery_app.task(bind=True, max_retries=3, soft_time_limit=60, time_limit=90)  # type: ignore[misc]
def process_webhook_event(
    self: Task,
    event_type: str,
    delivery_id: str,
    payload: dict[str, Any],
) -> dict[str, Any]:
    """
    Process a GitHub webhook event.

    Args:
        event_type: The GitHub event type (workflow_run, workflow_job, etc.)
        delivery_id: Unique delivery ID from GitHub
        payload: The webhook payload

    Returns:
        Dictionary with processing result
    """
    logger.info(
        "Processing webhook event",
        extra={
            "event_type": event_type,
            "delivery_id": delivery_id,
            "action": payload.get("action"),
        },
    )

    async def _process() -> dict[str, Any]:
        action = payload.get("action", "")

        # Check if event type is supported
        if event_type not in SUPPORTED_EVENTS:
            logger.info(
                f"Skipping unsupported event type: {event_type}",
                extra={"delivery_id": delivery_id},
            )
            return {
                "status": "skipped",
                "event_type": event_type,
                "action": action,
                "reason": "Unsupported event type",
            }

        # Route to appropriate handler
        if event_type == "workflow_run":
            return await _handle_workflow_run(payload, delivery_id, action)
        elif event_type == "workflow_job":
            return await _handle_workflow_job(payload, delivery_id, action)

        return {
            "status": "skipped",
            "event_type": event_type,
            "action": action,
            "reason": "No handler for event type",
        }

    try:
        return run_async(_process())
    except Exception as e:
        logger.error(
            f"Failed to process webhook event: {e}",
            extra={"delivery_id": delivery_id, "event_type": event_type},
        )
        raise self.retry(exc=e, countdown=30) from e


async def _handle_workflow_run(
    payload: dict[str, Any], delivery_id: str, action: str
) -> dict[str, Any]:
    """Handle workflow_run webhook events."""
    workflow_run = payload.get("workflow_run", {})
    repository = payload.get("repository", {})

    run_id = workflow_run.get("id")
    conclusion = workflow_run.get("conclusion")
    owner = repository.get("owner", {}).get("login", "")
    repo_name = repository.get("name", "")

    # Only process completed runs
    if action != "completed":
        logger.info(
            f"Skipping workflow_run with action: {action}",
            extra={"delivery_id": delivery_id, "run_id": run_id},
        )
        return {
            "status": "skipped",
            "event_type": "workflow_run",
            "action": action,
            "reason": "Only completed runs are processed",
        }

    triggered_tasks = []

    # Trigger processing for failed runs to fetch logs and analyze
    if conclusion == "failure":
        logger.info(
            f"Triggering run processing for failed run: {run_id}",
            extra={"delivery_id": delivery_id},
        )
        process_workflow_run.delay(owner, repo_name, run_id)
        triggered_tasks.append("process_workflow_run")

    return {
        "status": "processed",
        "event_type": "workflow_run",
        "action": action,
        "run_id": run_id,
        "conclusion": conclusion,
        "triggered_tasks": triggered_tasks,
    }


async def _handle_workflow_job(
    payload: dict[str, Any], delivery_id: str, action: str
) -> dict[str, Any]:
    """Handle workflow_job webhook events."""
    workflow_job = payload.get("workflow_job", {})

    job_id = workflow_job.get("id")
    run_id = workflow_job.get("run_id")
    conclusion = workflow_job.get("conclusion")

    # Only process completed jobs
    if action != "completed":
        logger.info(
            f"Skipping workflow_job with action: {action}",
            extra={"delivery_id": delivery_id, "job_id": job_id},
        )
        return {
            "status": "skipped",
            "event_type": "workflow_job",
            "action": action,
            "job_id": job_id,
            "reason": "Only completed jobs are processed",
        }

    triggered_tasks: list[str] = []

    # For failed jobs, we could trigger log fetching directly
    # But typically we process at the run level for completeness
    if conclusion == "failure":
        logger.info(
            f"Failed job detected: {job_id} in run {run_id}",
            extra={"delivery_id": delivery_id},
        )
        # The run-level processing will handle log fetching
        # We can still record the event for faster detection

    return {
        "status": "processed",
        "event_type": "workflow_job",
        "action": action,
        "job_id": job_id,
        "run_id": run_id,
        "conclusion": conclusion,
        "triggered_tasks": triggered_tasks,
    }

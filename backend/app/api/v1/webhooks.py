"""GitHub webhook endpoints."""

import json
import logging
from typing import Annotated

from fastapi import APIRouter, Depends, Header, Request, status
from fastapi.responses import JSONResponse

from app.application.services.webhook_processor import (
    GitHubWebhookValidator,
)
from app.config import Settings, get_settings
from app.core.exceptions import WebhookValidationError
from app.tasks.webhook_tasks import process_webhook_event

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/github")
async def github_webhook(
    request: Request,
    x_github_event: Annotated[str, Header()],
    x_hub_signature_256: Annotated[str, Header()],
    x_github_delivery: Annotated[str, Header()],
    settings: Annotated[Settings, Depends(get_settings)],
) -> JSONResponse:
    """
    Handle GitHub webhook events.

    Processes workflow_run and workflow_job events.
    Returns 202 Accepted and queues for async processing.
    """
    # Reject early when webhook secret is not configured
    if not settings.github_webhook_secret:
        logger.error("Webhook received but GITHUB_WEBHOOK_SECRET is not configured")
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={"detail": "Webhook validation is not configured"},
        )

    payload = await request.body()

    # Create validator using injected settings
    validator = GitHubWebhookValidator(settings.github_webhook_secret)

    try:
        # Validate signature
        if not validator.validate(payload, x_hub_signature_256):
            raise WebhookValidationError()

        # Parse payload
        data = json.loads(payload)
        action = data.get("action", "")

        logger.info(
            "Received GitHub webhook",
            extra={
                "event": x_github_event,
                "action": action,
                "delivery_id": x_github_delivery,
            },
        )

        # Queue for processing based on event type
        if x_github_event in ("workflow_run", "workflow_job"):
            process_webhook_event.delay(
                event_type=x_github_event,
                delivery_id=x_github_delivery,
                payload=data,
            )

        return JSONResponse(
            status_code=status.HTTP_202_ACCEPTED,
            content={
                "status": "queued",
                "delivery_id": x_github_delivery,
            },
        )

    except WebhookValidationError:
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={"detail": "Invalid webhook signature"},
        )

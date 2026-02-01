"""Notification API endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from app.domain.entities.notification import NotificationChannel, NotificationType

router = APIRouter()


class NotificationConfigCreate(BaseModel):
    """Request model for creating notification config."""

    channel: NotificationChannel
    webhook_url: str = Field(..., min_length=1)
    enabled: bool = True
    events: list[NotificationType] = Field(default_factory=list)
    repository_filter: list[str] = Field(default_factory=list)


class NotificationConfigResponse(BaseModel):
    """Response model for notification config."""

    channel: str
    enabled: bool
    events: list[str]
    repository_filter: list[str]
    webhook_configured: bool


class TestNotificationRequest(BaseModel):
    """Request model for testing notification."""

    channel: NotificationChannel
    message: str = "This is a test notification from GitHub Actions Dashboard"


class TestNotificationResponse(BaseModel):
    """Response model for test notification result."""

    success: bool
    channel: str
    message: str
    error: str | None = None


class NotificationStatsResponse(BaseModel):
    """Response model for notification statistics."""

    total_sent: int
    total_failed: int
    pending: int
    by_channel: dict[str, dict[str, int]]
    by_type: dict[str, int]


# In-memory storage for configs (in production, use database)
_notification_configs: dict[NotificationChannel, dict] = {}


@router.get("/configs", response_model=list[NotificationConfigResponse])
async def list_notification_configs() -> list[NotificationConfigResponse]:
    """List all notification configurations."""
    configs = []
    for channel, config in _notification_configs.items():
        configs.append(
            NotificationConfigResponse(
                channel=channel.value,
                enabled=config.get("enabled", False),
                events=[e.value for e in config.get("events", [])],
                repository_filter=config.get("repository_filter", []),
                webhook_configured=bool(config.get("webhook_url")),
            )
        )
    return configs


@router.post("/configs", response_model=NotificationConfigResponse, status_code=status.HTTP_201_CREATED)
async def create_notification_config(
    config: NotificationConfigCreate,
) -> NotificationConfigResponse:
    """Create or update notification configuration."""
    _notification_configs[config.channel] = {
        "webhook_url": config.webhook_url,
        "enabled": config.enabled,
        "events": config.events,
        "repository_filter": config.repository_filter,
    }

    return NotificationConfigResponse(
        channel=config.channel.value,
        enabled=config.enabled,
        events=[e.value for e in config.events],
        repository_filter=config.repository_filter,
        webhook_configured=True,
    )


@router.delete("/configs/{channel}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_notification_config(channel: NotificationChannel) -> None:
    """Delete notification configuration."""
    if channel in _notification_configs:
        del _notification_configs[channel]


@router.post("/test", response_model=TestNotificationResponse)
async def test_notification(request: TestNotificationRequest) -> TestNotificationResponse:
    """Send a test notification to verify configuration."""
    config = _notification_configs.get(request.channel)

    if not config or not config.get("webhook_url"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"No webhook configured for channel: {request.channel.value}",
        )

    # Import here to avoid circular imports
    from app.application.services.notification_service import (
        SlackSender,
        DiscordSender,
        WebhookSender,
    )
    from app.domain.entities.notification import Notification

    # Create test notification
    notification = Notification.create(
        notification_type=NotificationType.WORKFLOW_SUCCEEDED,
        channel=request.channel,
        title="Test Notification",
        message=request.message,
        metadata={"test": True, "source": "API"},
    )

    # Get appropriate sender
    webhook_url = config["webhook_url"]
    if request.channel == NotificationChannel.SLACK:
        sender = SlackSender(webhook_url)
    elif request.channel == NotificationChannel.DISCORD:
        sender = DiscordSender(webhook_url)
    else:
        sender = WebhookSender(webhook_url)

    # Send test notification
    result = await sender.send(notification)

    return TestNotificationResponse(
        success=result.success,
        channel=request.channel.value,
        message=result.message if result.success else "Failed to send",
        error=result.error,
    )


@router.get("/stats", response_model=NotificationStatsResponse)
async def get_notification_stats() -> NotificationStatsResponse:
    """Get notification statistics."""
    # In a real implementation, this would query the database
    return NotificationStatsResponse(
        total_sent=0,
        total_failed=0,
        pending=0,
        by_channel={},
        by_type={},
    )


@router.post("/trigger/workflow-failed")
async def trigger_workflow_failed_notification(
    repository_name: str,
    workflow_name: str,
    run_number: int,
    branch: str,
    commit_sha: str,
    actor: str,
    run_url: str = "",
    failure_reason: str = "",
) -> dict:
    """Manually trigger a workflow failed notification."""
    from app.application.services.notification_service import (
        NotificationService,
        NotificationConfig,
    )
    from app.domain.entities.notification import WorkflowFailedPayload

    # Build configs from stored configs
    configs = [
        NotificationConfig(
            channel=channel,
            webhook_url=cfg.get("webhook_url", ""),
            enabled=cfg.get("enabled", False),
            events=cfg.get("events", []),
            repository_filter=cfg.get("repository_filter", []),
        )
        for channel, cfg in _notification_configs.items()
    ]

    if not configs:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No notification channels configured",
        )

    service = NotificationService(configs)
    payload = WorkflowFailedPayload(
        repository_name=repository_name,
        workflow_name=workflow_name,
        run_number=run_number,
        branch=branch,
        commit_sha=commit_sha,
        actor=actor,
        run_url=run_url,
        failure_reason=failure_reason,
    )

    results = await service.notify_workflow_failed(payload)

    return {
        "sent": {k.value: v.success for k, v in results.items()},
        "errors": {k.value: v.error for k, v in results.items() if v.error},
    }

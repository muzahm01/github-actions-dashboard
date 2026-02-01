"""Celery tasks for notifications."""

from __future__ import annotations

import logging
from datetime import datetime, timedelta

from app.tasks.celery_app import celery_app

logger = logging.getLogger(__name__)


@celery_app.task(
    name="tasks.send_notification",
    bind=True,
    max_retries=3,
    default_retry_delay=60,
)
def send_notification_task(
    self,
    notification_type: str,
    title: str,
    message: str,
    metadata: dict | None = None,
    channels: list[str] | None = None,
) -> dict:
    """Send notification via configured channels.

    Args:
        notification_type: Type of notification (workflow_failed, etc.)
        title: Notification title
        message: Notification message body
        metadata: Additional metadata dict
        channels: Optional list of channels to send to

    Returns:
        Dict with send results per channel
    """
    import asyncio
    from app.domain.entities.notification import NotificationChannel, NotificationType

    async def _send():
        # Import inside to avoid circular imports
        from app.application.services.notification_service import (
            NotificationService,
            NotificationConfig,
        )
        from app.config import get_settings

        settings = get_settings()

        # Build configs from settings
        configs = []

        if settings.slack_webhook_url:
            configs.append(
                NotificationConfig(
                    channel=NotificationChannel.SLACK,
                    webhook_url=settings.slack_webhook_url,
                    enabled=True,
                )
            )

        if settings.discord_webhook_url:
            configs.append(
                NotificationConfig(
                    channel=NotificationChannel.DISCORD,
                    webhook_url=settings.discord_webhook_url,
                    enabled=True,
                )
            )

        if not configs:
            logger.warning("No notification channels configured")
            return {"status": "skipped", "reason": "No channels configured"}

        service = NotificationService(configs)

        # Convert string types to enums
        notif_type = NotificationType(notification_type)
        target_channels = (
            [NotificationChannel(c) for c in channels] if channels else None
        )

        results = await service.notify(
            notification_type=notif_type,
            title=title,
            message=message,
            metadata=metadata,
            channels=target_channels,
        )

        return {
            channel.value: {
                "success": result.success,
                "message": result.message,
                "error": result.error,
            }
            for channel, result in results.items()
        }

    try:
        return asyncio.run(_send())
    except Exception as e:
        logger.error(f"Failed to send notification: {e}")
        raise self.retry(exc=e)


@celery_app.task(name="tasks.send_workflow_failed_notification")
def send_workflow_failed_notification_task(
    repository_name: str,
    workflow_name: str,
    run_number: int,
    branch: str,
    commit_sha: str,
    actor: str,
    run_url: str = "",
    failure_reason: str = "",
) -> dict:
    """Send workflow failed notification.

    This is a convenience task that formats the notification properly.
    """
    import asyncio
    from app.domain.entities.notification import NotificationChannel, WorkflowFailedPayload

    async def _send():
        from app.application.services.notification_service import (
            NotificationService,
            NotificationConfig,
        )
        from app.config import get_settings

        settings = get_settings()
        configs = []

        if settings.slack_webhook_url:
            configs.append(
                NotificationConfig(
                    channel=NotificationChannel.SLACK,
                    webhook_url=settings.slack_webhook_url,
                    enabled=True,
                )
            )

        if settings.discord_webhook_url:
            configs.append(
                NotificationConfig(
                    channel=NotificationChannel.DISCORD,
                    webhook_url=settings.discord_webhook_url,
                    enabled=True,
                )
            )

        if not configs:
            return {"status": "skipped", "reason": "No channels configured"}

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
            channel.value: result.success
            for channel, result in results.items()
        }

    return asyncio.run(_send())


@celery_app.task(name="tasks.send_daily_summary")
def send_daily_summary_task() -> dict:
    """Send daily summary notification.

    This task should be scheduled to run once daily.
    """
    import asyncio
    from app.domain.entities.notification import NotificationChannel, DailySummaryPayload

    async def _send():
        from app.application.services.notification_service import (
            NotificationService,
            NotificationConfig,
        )
        from app.config import get_settings

        settings = get_settings()
        configs = []

        if settings.slack_webhook_url:
            configs.append(
                NotificationConfig(
                    channel=NotificationChannel.SLACK,
                    webhook_url=settings.slack_webhook_url,
                    enabled=True,
                )
            )

        if settings.discord_webhook_url:
            configs.append(
                NotificationConfig(
                    channel=NotificationChannel.DISCORD,
                    webhook_url=settings.discord_webhook_url,
                    enabled=True,
                )
            )

        if not configs:
            return {"status": "skipped", "reason": "No channels configured"}

        # Calculate summary data
        # In a real implementation, this would query the database
        yesterday = datetime.utcnow() - timedelta(days=1)

        payload = DailySummaryPayload(
            date=yesterday.strftime("%Y-%m-%d"),
            total_runs=0,  # Would be calculated from DB
            successful_runs=0,
            failed_runs=0,
            success_rate=0.0,
            top_failures=[],
            repositories_monitored=0,
        )

        service = NotificationService(configs)
        results = await service.notify_daily_summary(payload)

        return {
            channel.value: result.success
            for channel, result in results.items()
        }

    return asyncio.run(_send())


@celery_app.task(name="tasks.process_pending_notifications")
def process_pending_notifications_task() -> dict:
    """Process pending/failed notifications for retry."""
    import asyncio

    async def _process():
        from app.application.services.notification_service import (
            NotificationService,
            NotificationConfig,
        )
        from app.domain.entities.notification import NotificationChannel
        from app.config import get_settings

        settings = get_settings()
        configs = []

        if settings.slack_webhook_url:
            configs.append(
                NotificationConfig(
                    channel=NotificationChannel.SLACK,
                    webhook_url=settings.slack_webhook_url,
                    enabled=True,
                )
            )

        if settings.discord_webhook_url:
            configs.append(
                NotificationConfig(
                    channel=NotificationChannel.DISCORD,
                    webhook_url=settings.discord_webhook_url,
                    enabled=True,
                )
            )

        if not configs:
            return {"processed": 0, "reason": "No channels configured"}

        service = NotificationService(configs)
        processed = await service.process_pending()

        return {"processed": processed}

    return asyncio.run(_process())

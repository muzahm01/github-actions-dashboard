"""Redis pub/sub bridge for WebSocket notifications from Celery tasks."""

import asyncio
import json
import logging
from contextlib import suppress
from typing import Any

import redis.asyncio as aioredis

from app.config import get_settings
from app.infrastructure.websocket.manager import connection_manager

logger = logging.getLogger(__name__)
settings = get_settings()


class WebSocketPubSub:
    """Redis pub/sub for broadcasting from Celery to WebSocket clients."""

    CHANNEL = "websocket:broadcasts"

    def __init__(self) -> None:
        """Initialize pub/sub connection."""
        self.redis_client: aioredis.Redis | None = None
        self.pubsub: aioredis.client.PubSub | None = None
        self.listening_task: asyncio.Task[None] | None = None

    async def connect(self) -> None:
        """Connect to Redis and subscribe to broadcast channel."""
        try:
            self.redis_client = aioredis.from_url(  # type: ignore[no-untyped-call]
                str(settings.redis_url),
                encoding="utf-8",
                decode_responses=True,
            )
            if self.redis_client:
                self.pubsub = self.redis_client.pubsub()
                await self.pubsub.subscribe(self.CHANNEL)
                logger.info(f"Subscribed to Redis channel: {self.CHANNEL}")

                # Start listening task
                self.listening_task = asyncio.create_task(self._listen())
        except Exception as e:
            logger.error(f"Failed to connect to Redis pub/sub: {e}")

    async def disconnect(self) -> None:
        """Disconnect from Redis."""
        if self.listening_task:
            self.listening_task.cancel()
            with suppress(asyncio.CancelledError):
                await self.listening_task

        if self.pubsub:
            await self.pubsub.unsubscribe(self.CHANNEL)
            await self.pubsub.close()

        if self.redis_client:
            await self.redis_client.close()

        logger.info("Disconnected from Redis pub/sub")

    async def _listen(self) -> None:
        """Listen for messages and broadcast to WebSocket clients."""
        if not self.pubsub:
            return

        try:
            async for message in self.pubsub.listen():
                if message["type"] == "message":
                    try:
                        data = json.loads(message["data"])
                        await connection_manager.broadcast(data)
                    except json.JSONDecodeError:
                        logger.error(f"Invalid JSON in pubsub message: {message['data']}")
                    except Exception as e:
                        logger.error(f"Error broadcasting pubsub message: {e}")
        except asyncio.CancelledError:
            logger.info("Pub/sub listener cancelled")
        except Exception as e:
            logger.error(f"Error in pub/sub listener: {e}")


# Global pub/sub instance
pubsub_manager = WebSocketPubSub()


# Helper functions for publishing from Celery tasks
def publish_workflow_run_update(
    run_id: int,
    status: str,
    conclusion: str | None = None,
    data: dict[str, Any] | None = None,
) -> None:
    """Publish workflow run update (can be called from Celery tasks)."""
    import redis

    try:
        r = redis.from_url(str(settings.redis_url))  # type: ignore[no-untyped-call]
        message = {
            "type": "workflow_run_update",
            "run_id": run_id,
            "status": status,
            "conclusion": conclusion,
            "data": data or {},
        }
        r.publish(WebSocketPubSub.CHANNEL, json.dumps(message))
        r.close()
    except Exception as e:
        logger.error(f"Failed to publish workflow run update: {e}")


def publish_job_update(
    job_id: int,
    run_id: int,
    status: str,
    conclusion: str | None = None,
    data: dict[str, Any] | None = None,
) -> None:
    """Publish job update (can be called from Celery tasks)."""
    import redis

    try:
        r = redis.from_url(str(settings.redis_url))  # type: ignore[no-untyped-call]
        message = {
            "type": "job_update",
            "job_id": job_id,
            "run_id": run_id,
            "status": status,
            "conclusion": conclusion,
            "data": data or {},
        }
        r.publish(WebSocketPubSub.CHANNEL, json.dumps(message))
        r.close()
    except Exception as e:
        logger.error(f"Failed to publish job update: {e}")


def publish_analysis_complete(
    log_id: int,
    analysis_id: int,
    data: dict[str, Any] | None = None,
) -> None:
    """Publish analysis completion (can be called from Celery tasks)."""
    import redis

    try:
        r = redis.from_url(str(settings.redis_url))  # type: ignore[no-untyped-call]
        message = {
            "type": "analysis_complete",
            "log_id": log_id,
            "analysis_id": analysis_id,
            "data": data or {},
        }
        r.publish(WebSocketPubSub.CHANNEL, json.dumps(message))
        r.close()
    except Exception as e:
        logger.error(f"Failed to publish analysis complete: {e}")

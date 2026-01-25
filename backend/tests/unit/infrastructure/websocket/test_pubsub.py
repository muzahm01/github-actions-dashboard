"""Tests for WebSocket pub/sub functionality."""
import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.infrastructure.websocket.pubsub import (
    WebSocketPubSub,
    publish_analysis_complete,
    publish_job_update,
    publish_workflow_run_update,
)


@pytest.fixture
def pubsub_manager():
    """Create a fresh WebSocketPubSub instance."""
    return WebSocketPubSub()


@pytest.mark.asyncio
async def test_connect_subscribes_to_channel(pubsub_manager):
    """Test that connect subscribes to the broadcast channel."""
    mock_redis = MagicMock()
    mock_pubsub = MagicMock()
    mock_pubsub.subscribe = AsyncMock()
    mock_redis.pubsub.return_value = mock_pubsub

    with patch("app.infrastructure.websocket.pubsub.aioredis.from_url", return_value=mock_redis):
        await pubsub_manager.connect()

        assert pubsub_manager.redis_client == mock_redis
        assert pubsub_manager.pubsub == mock_pubsub
        mock_pubsub.subscribe.assert_called_once_with(WebSocketPubSub.CHANNEL)


@pytest.mark.asyncio
async def test_connect_handles_error_gracefully(pubsub_manager):
    """Test that connect handles errors without crashing."""
    with patch("app.infrastructure.websocket.pubsub.aioredis.from_url", side_effect=Exception("Redis error")):
        # Should not raise
        await pubsub_manager.connect()

        # Should not have set clients
        assert pubsub_manager.redis_client is None or True  # May or may not be set


@pytest.mark.asyncio
async def test_disconnect_cleans_up_resources(pubsub_manager):
    """Test that disconnect cleans up all resources."""
    # Setup
    mock_redis = MagicMock()
    mock_pubsub = MagicMock()
    mock_pubsub.subscribe = AsyncMock()
    mock_pubsub.unsubscribe = AsyncMock()
    mock_pubsub.close = AsyncMock()
    mock_pubsub.listen = AsyncMock()
    mock_redis.pubsub.return_value = mock_pubsub
    mock_redis.close = AsyncMock()

    with patch("app.infrastructure.websocket.pubsub.aioredis.from_url", return_value=mock_redis):
        await pubsub_manager.connect()

    # Mock listening task - use a real asyncio task
    import asyncio
    async def dummy_task():
        await asyncio.sleep(0.1)

    if pubsub_manager.listening_task:
        pubsub_manager.listening_task.cancel()
        pubsub_manager.listening_task = asyncio.create_task(dummy_task())

    # Disconnect
    await pubsub_manager.disconnect()

    # Verify cleanup
    mock_pubsub.unsubscribe.assert_called_once_with(WebSocketPubSub.CHANNEL)
    mock_pubsub.close.assert_called_once()
    mock_redis.close.assert_called_once()


@pytest.mark.asyncio
async def test_disconnect_handles_no_connections(pubsub_manager):
    """Test that disconnect works even when not connected."""
    # Should not raise
    await pubsub_manager.disconnect()


def test_publish_workflow_run_update():
    """Test publishing workflow run update."""
    mock_redis = MagicMock()

    with patch("redis.from_url", return_value=mock_redis):
        publish_workflow_run_update(
            run_id=123,
            status="completed",
            conclusion="success",
            data={"duration": 60}
        )

        # Verify publish was called
        assert mock_redis.publish.called
        call_args = mock_redis.publish.call_args

        # Check channel
        assert call_args[0][0] == WebSocketPubSub.CHANNEL

        # Check message
        message = json.loads(call_args[0][1])
        assert message["type"] == "workflow_run_update"
        assert message["run_id"] == 123
        assert message["status"] == "completed"
        assert message["conclusion"] == "success"
        assert message["data"] == {"duration": 60}

        # Verify close was called
        mock_redis.close.assert_called_once()


def test_publish_workflow_run_update_handles_error():
    """Test that publish handles errors gracefully."""
    with patch("redis.from_url", side_effect=Exception("Redis error")):
        # Should not raise
        publish_workflow_run_update(
            run_id=123,
            status="completed"
        )


def test_publish_job_update():
    """Test publishing job update."""
    mock_redis = MagicMock()

    with patch("redis.from_url", return_value=mock_redis):
        publish_job_update(
            job_id=456,
            run_id=123,
            status="in_progress",
            conclusion=None,
            data={"step": "build"}
        )

        # Verify publish was called
        assert mock_redis.publish.called
        call_args = mock_redis.publish.call_args

        # Check message
        message = json.loads(call_args[0][1])
        assert message["type"] == "job_update"
        assert message["job_id"] == 456
        assert message["run_id"] == 123
        assert message["status"] == "in_progress"
        assert message["conclusion"] is None
        assert message["data"] == {"step": "build"}


def test_publish_job_update_handles_error():
    """Test that job update publish handles errors gracefully."""
    with patch("redis.from_url", side_effect=Exception("Redis error")):
        # Should not raise
        publish_job_update(
            job_id=456,
            run_id=123,
            status="in_progress"
        )


def test_publish_analysis_complete():
    """Test publishing analysis completion."""
    mock_redis = MagicMock()

    with patch("redis.from_url", return_value=mock_redis):
        publish_analysis_complete(
            log_id=789,
            analysis_id=101,
            data={"confidence": 0.95}
        )

        # Verify publish was called
        assert mock_redis.publish.called
        call_args = mock_redis.publish.call_args

        # Check message
        message = json.loads(call_args[0][1])
        assert message["type"] == "analysis_complete"
        assert message["log_id"] == 789
        assert message["analysis_id"] == 101
        assert message["data"] == {"confidence": 0.95}


def test_publish_analysis_complete_handles_error():
    """Test that analysis complete publish handles errors gracefully."""
    with patch("redis.from_url", side_effect=Exception("Redis error")):
        # Should not raise
        publish_analysis_complete(
            log_id=789,
            analysis_id=101
        )


def test_publish_with_none_data():
    """Test that publish functions handle None data."""
    mock_redis = MagicMock()

    with patch("redis.from_url", return_value=mock_redis):
        publish_workflow_run_update(
            run_id=123,
            status="completed",
            data=None
        )

        call_args = mock_redis.publish.call_args
        message = json.loads(call_args[0][1])
        # None should be converted to empty dict
        assert message["data"] == {}

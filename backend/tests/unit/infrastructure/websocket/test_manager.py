"""Tests for WebSocket connection manager."""
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.infrastructure.websocket.manager import ConnectionManager


@pytest.fixture
def connection_manager():
    """Create a fresh connection manager for each test."""
    return ConnectionManager()


@pytest.fixture
def mock_websocket():
    """Create a mock WebSocket connection."""
    websocket = MagicMock()
    websocket.accept = AsyncMock()
    websocket.send_json = AsyncMock()
    return websocket


@pytest.mark.asyncio
async def test_connect_websocket(connection_manager, mock_websocket):
    """Test connecting a WebSocket."""
    await connection_manager.connect(mock_websocket)

    mock_websocket.accept.assert_called_once()
    assert mock_websocket in connection_manager.active_connections
    assert len(connection_manager.active_connections) == 1


@pytest.mark.asyncio
async def test_disconnect_websocket(connection_manager, mock_websocket):
    """Test disconnecting a WebSocket."""
    await connection_manager.connect(mock_websocket)
    connection_manager.disconnect(mock_websocket)

    assert mock_websocket not in connection_manager.active_connections
    assert len(connection_manager.active_connections) == 0


@pytest.mark.asyncio
async def test_disconnect_not_connected_websocket(connection_manager, mock_websocket):
    """Test disconnecting a WebSocket that was never connected."""
    # Should not raise an error
    connection_manager.disconnect(mock_websocket)
    assert len(connection_manager.active_connections) == 0


@pytest.mark.asyncio
async def test_send_personal_message(connection_manager, mock_websocket):
    """Test sending a message to a specific WebSocket."""
    await connection_manager.connect(mock_websocket)

    message = {"type": "test", "data": "hello"}
    await connection_manager.send_personal_message(message, mock_websocket)

    mock_websocket.send_json.assert_called_once_with(message)


@pytest.mark.asyncio
async def test_send_personal_message_handles_error(connection_manager, mock_websocket):
    """Test that send_personal_message handles errors gracefully."""
    await connection_manager.connect(mock_websocket)
    mock_websocket.send_json.side_effect = Exception("Connection error")

    message = {"type": "test", "data": "hello"}
    await connection_manager.send_personal_message(message, mock_websocket)

    # Should disconnect on error
    assert mock_websocket not in connection_manager.active_connections


@pytest.mark.asyncio
async def test_broadcast_to_all_connections(connection_manager):
    """Test broadcasting a message to all connected WebSockets."""
    # Create multiple mock websockets
    ws1 = MagicMock()
    ws1.accept = AsyncMock()
    ws1.send_json = AsyncMock()

    ws2 = MagicMock()
    ws2.accept = AsyncMock()
    ws2.send_json = AsyncMock()

    await connection_manager.connect(ws1)
    await connection_manager.connect(ws2)

    message = {"type": "test", "data": "broadcast"}
    await connection_manager.broadcast(message)

    ws1.send_json.assert_called_once_with(message)
    ws2.send_json.assert_called_once_with(message)


@pytest.mark.asyncio
async def test_broadcast_handles_disconnected_clients(connection_manager):
    """Test that broadcast removes disconnected clients."""
    ws1 = MagicMock()
    ws1.accept = AsyncMock()
    ws1.send_json = AsyncMock()

    ws2 = MagicMock()
    ws2.accept = AsyncMock()
    ws2.send_json = AsyncMock(side_effect=Exception("Connection lost"))

    await connection_manager.connect(ws1)
    await connection_manager.connect(ws2)

    message = {"type": "test", "data": "broadcast"}
    await connection_manager.broadcast(message)

    # ws2 should be disconnected
    assert ws1 in connection_manager.active_connections
    assert ws2 not in connection_manager.active_connections
    assert len(connection_manager.active_connections) == 1


@pytest.mark.asyncio
async def test_broadcast_workflow_run_update(connection_manager, mock_websocket):
    """Test broadcasting workflow run update."""
    await connection_manager.connect(mock_websocket)

    await connection_manager.broadcast_workflow_run_update(
        run_id=123,
        status="completed",
        conclusion="success",
        data={"duration": 60}
    )

    expected_message = {
        "type": "workflow_run_update",
        "run_id": 123,
        "status": "completed",
        "conclusion": "success",
        "data": {"duration": 60}
    }
    mock_websocket.send_json.assert_called_once_with(expected_message)


@pytest.mark.asyncio
async def test_broadcast_job_update(connection_manager, mock_websocket):
    """Test broadcasting job update."""
    await connection_manager.connect(mock_websocket)

    await connection_manager.broadcast_job_update(
        job_id=456,
        run_id=123,
        status="in_progress",
        conclusion=None,
        data={"step": "build"}
    )

    expected_message = {
        "type": "job_update",
        "job_id": 456,
        "run_id": 123,
        "status": "in_progress",
        "conclusion": None,
        "data": {"step": "build"}
    }
    mock_websocket.send_json.assert_called_once_with(expected_message)


@pytest.mark.asyncio
async def test_broadcast_analysis_complete(connection_manager, mock_websocket):
    """Test broadcasting analysis completion."""
    await connection_manager.connect(mock_websocket)

    await connection_manager.broadcast_analysis_complete(
        log_id=789,
        analysis_id=101,
        data={"confidence": 0.95}
    )

    expected_message = {
        "type": "analysis_complete",
        "log_id": 789,
        "analysis_id": 101,
        "data": {"confidence": 0.95}
    }
    mock_websocket.send_json.assert_called_once_with(expected_message)


@pytest.mark.asyncio
async def test_broadcast_skips_ping_logging(connection_manager, mock_websocket):
    """Test that ping messages don't clutter logs."""
    await connection_manager.connect(mock_websocket)

    # Ping messages should still be sent but with different logging behavior
    await connection_manager.broadcast({"type": "ping"})

    mock_websocket.send_json.assert_called_once_with({"type": "ping"})

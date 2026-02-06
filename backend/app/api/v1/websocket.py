"""WebSocket endpoints for real-time updates."""

import logging
from typing import Any

from fastapi import APIRouter, Query, WebSocket, WebSocketDisconnect

from app.infrastructure.websocket.manager import connection_manager

logger = logging.getLogger(__name__)
router = APIRouter()


@router.websocket("/ws")
async def websocket_endpoint(
    websocket: WebSocket,
    token: str | None = Query(default=None),
) -> None:
    """
    WebSocket endpoint for real-time updates.

    Clients connect to this endpoint to receive live updates about:
    - Workflow run status changes
    - Job status changes
    - Error analysis completions
    - Test result parsing completions

    Protocol:
    - Client sends: {"type": "ping"} to keep connection alive
    - Server sends: {"type": "pong"} in response
    - Server broadcasts: Various event types with relevant data

    In production, supply ?token=<api-key> for authentication.
    """
    connected = await connection_manager.connect(websocket, token=token)
    if not connected:
        return
    try:
        while True:
            # Receive messages from client (mostly for ping/pong)
            data = await websocket.receive_json()

            # Handle ping
            if data.get("type") == "ping":
                await connection_manager.send_personal_message(
                    {"type": "pong", "timestamp": data.get("timestamp")},
                    websocket,
                )

            # Handle subscription to specific resources
            elif data.get("type") == "subscribe":
                # Future enhancement: subscribe to specific runs/workflows
                await connection_manager.send_personal_message(
                    {
                        "type": "subscribed",
                        "resource": data.get("resource"),
                        "id": data.get("id"),
                    },
                    websocket,
                )

            # Handle unsubscribe
            elif data.get("type") == "unsubscribe":
                await connection_manager.send_personal_message(
                    {
                        "type": "unsubscribed",
                        "resource": data.get("resource"),
                        "id": data.get("id"),
                    },
                    websocket,
                )

    except WebSocketDisconnect:
        logger.info("Client disconnected normally")
        connection_manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        connection_manager.disconnect(websocket)


@router.get("/ws/stats")
async def websocket_stats() -> dict[str, Any]:
    """Get WebSocket connection statistics."""
    return {
        "active_connections": len(connection_manager.active_connections),
        "status": "healthy"
        if len(connection_manager.active_connections) >= 0
        else "no_connections",
    }

"""WebSocket endpoints for real-time updates."""

import logging
from typing import Any

from fastapi import APIRouter, Query, WebSocket, WebSocketDisconnect

from app.infrastructure.websocket.manager import connection_manager

logger = logging.getLogger(__name__)
router = APIRouter()

# Subprotocol prefix used to pass the API key via Sec-WebSocket-Protocol.
# Example client: ``new WebSocket(url, ["api-key.<token>"])``.
_AUTH_SUBPROTOCOL_PREFIX = "api-key."


def _extract_token_from_subprotocols(websocket: WebSocket) -> tuple[str | None, str | None]:
    """Return (token, subprotocol_to_echo) from Sec-WebSocket-Protocol, if any."""
    raw = websocket.headers.get("sec-websocket-protocol")
    if not raw:
        return None, None
    for offered in (p.strip() for p in raw.split(",")):
        if offered.startswith(_AUTH_SUBPROTOCOL_PREFIX):
            return offered[len(_AUTH_SUBPROTOCOL_PREFIX):], offered
    return None, None


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

    Authentication (production):
    - Preferred: supply the API key via the ``Sec-WebSocket-Protocol`` header
      using the subprotocol ``api-key.<token>`` (e.g. JS:
      ``new WebSocket(url, ["api-key.<token>"])``).
    - Deprecated: the ``?token=<api-key>`` query parameter is still accepted
      for backward compatibility, but tokens in URLs end up in access logs,
      browser history, and upstream proxies — migrate clients to the
      subprotocol form.
    """
    subprotocol_token, echo_subprotocol = _extract_token_from_subprotocols(websocket)
    if subprotocol_token is not None:
        auth_token: str | None = subprotocol_token
    else:
        if token is not None:
            logger.warning(
                "WebSocket client sent auth token in URL query string; "
                "this is deprecated — use the 'api-key.<token>' subprotocol instead."
            )
        auth_token = token

    connected = await connection_manager.connect(
        websocket, token=auth_token, subprotocol=echo_subprotocol
    )
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

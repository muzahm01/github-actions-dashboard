"""WebSocket connection manager for real-time updates."""

import logging
import secrets
from typing import Any

from fastapi import WebSocket

logger = logging.getLogger(__name__)

# Default max connections — can be overridden from config
MAX_WS_CONNECTIONS = 100


class ConnectionManager:
    """Manage WebSocket connections and broadcasts."""

    def __init__(self, max_connections: int = MAX_WS_CONNECTIONS) -> None:
        """Initialize connection manager."""
        self.active_connections: list[WebSocket] = []
        self._max_connections = max_connections

    async def connect(self, websocket: WebSocket, token: str | None = None) -> bool:
        """Accept and store a new WebSocket connection.

        Returns True if the connection was accepted, False otherwise.
        Enforces a maximum connection limit and optional token auth.
        """
        # Enforce connection limit to prevent resource exhaustion
        if len(self.active_connections) >= self._max_connections:
            await websocket.close(code=1013)  # Try Again Later
            logger.warning("WebSocket rejected: max connections reached")
            return False

        # Token auth — skip only when dev auth bypass is explicitly enabled
        from app.config import get_settings

        settings = get_settings()
        skip_auth = (
            settings.environment in ("development", "testing") and settings.enable_dev_auth_bypass
        )
        if not skip_auth and (not token or not secrets.compare_digest(token, settings.secret_key)):
            await websocket.close(code=1008)  # Policy Violation
            logger.warning("WebSocket rejected: invalid or missing token")
            return False

        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info(f"WebSocket connected. Total connections: {len(self.active_connections)}")
        return True

    def disconnect(self, websocket: WebSocket) -> None:
        """Remove a WebSocket connection."""
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
        logger.info(f"WebSocket disconnected. Total connections: {len(self.active_connections)}")

    async def send_personal_message(self, message: dict[str, Any], websocket: WebSocket) -> None:
        """Send a message to a specific WebSocket connection."""
        try:
            await websocket.send_json(message)
        except Exception as e:
            logger.error(f"Error sending personal message: {e}")
            self.disconnect(websocket)

    async def broadcast(self, message: dict[str, Any]) -> None:
        """Broadcast a message to all connected clients."""
        disconnected: list[WebSocket] = []

        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception as e:
                logger.error(f"Error broadcasting to connection: {e}")
                disconnected.append(connection)

        # Clean up disconnected connections
        for connection in disconnected:
            self.disconnect(connection)

        if message.get("type") != "ping":  # Don't log pings
            logger.debug(
                f"Broadcasted {message.get('type')} to {len(self.active_connections)} connections"
            )

    async def broadcast_workflow_run_update(
        self,
        run_id: int,
        status: str,
        conclusion: str | None = None,
        data: dict[str, Any] | None = None,
    ) -> None:
        """Broadcast workflow run status update."""
        message = {
            "type": "workflow_run_update",
            "run_id": run_id,
            "status": status,
            "conclusion": conclusion,
            "data": data or {},
        }
        await self.broadcast(message)

    async def broadcast_job_update(
        self,
        job_id: int,
        run_id: int,
        status: str,
        conclusion: str | None = None,
        data: dict[str, Any] | None = None,
    ) -> None:
        """Broadcast job status update."""
        message = {
            "type": "job_update",
            "job_id": job_id,
            "run_id": run_id,
            "status": status,
            "conclusion": conclusion,
            "data": data or {},
        }
        await self.broadcast(message)

    async def broadcast_analysis_complete(
        self,
        log_id: int,
        analysis_id: int,
        data: dict[str, Any] | None = None,
    ) -> None:
        """Broadcast error analysis completion."""
        message = {
            "type": "analysis_complete",
            "log_id": log_id,
            "analysis_id": analysis_id,
            "data": data or {},
        }
        await self.broadcast(message)


# Global connection manager instance
connection_manager = ConnectionManager()

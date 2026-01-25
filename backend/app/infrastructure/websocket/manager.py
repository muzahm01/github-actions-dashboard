"""WebSocket connection manager for real-time updates."""
import logging
from typing import Any

from fastapi import WebSocket

logger = logging.getLogger(__name__)


class ConnectionManager:
    """Manage WebSocket connections and broadcasts."""

    def __init__(self) -> None:
        """Initialize connection manager."""
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket) -> None:
        """Accept and store a new WebSocket connection."""
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info(f"WebSocket connected. Total connections: {len(self.active_connections)}")

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

"""
websocket_manager.py — WebSocket connection manager.

Responsibilities:
  • Track all active WebSocket connections
  • Broadcast STATE_CHANGED events to every connected client
  • Clean up disconnected clients silently

FastAPI endpoint (defined in main.py) calls connect/disconnect.
The event bus calls on_state_changed when state transitions occur.
"""

import json
import logging
from typing import Any

from fastapi import WebSocket

from events.event_types import EventType

logger = logging.getLogger(__name__)


class WebSocketManager:
    def __init__(self) -> None:
        self._connections: set[WebSocket] = set()

    # ------------------------------------------------------------------
    # Connection lifecycle (called by FastAPI WS route)
    # ------------------------------------------------------------------

    async def connect(self, ws: WebSocket) -> None:
        await ws.accept()
        self._connections.add(ws)
        logger.info("WS client connected — total=%d", len(self._connections))

    def disconnect(self, ws: WebSocket) -> None:
        self._connections.discard(ws)
        logger.info("WS client disconnected — total=%d", len(self._connections))

    # ------------------------------------------------------------------
    # Event bus handler
    # ------------------------------------------------------------------

    async def on_state_changed(self, _event_type: EventType, data: Any) -> None:
        """Broadcast the new state to every connected client."""
        payload = json.dumps({"event": "STATE_CHANGED", "state": str(data)})
        await self._broadcast(payload)

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    async def _broadcast(self, message: str) -> None:
        dead: set[WebSocket] = set()
        for ws in self._connections:
            try:
                await ws.send_text(message)
            except Exception:
                logger.warning("WS send failed — marking client for removal")
                dead.add(ws)
        self._connections -= dead

    @property
    def connection_count(self) -> int:
        return len(self._connections)

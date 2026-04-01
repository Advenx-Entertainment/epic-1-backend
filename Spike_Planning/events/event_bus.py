"""
event_bus.py — Central publish/subscribe hub.

No module calls another module directly.
Every interaction flows through emit().

Usage:
    bus = EventBus()
    bus.subscribe(EventType.STATE_CHANGED, my_handler)
    await bus.emit(EventType.STATE_CHANGED, {"state": "PLANTING"})
"""

import asyncio
import logging
from collections import defaultdict
from typing import Any, Awaitable, Callable

from events.event_types import EventType

logger = logging.getLogger(__name__)

Handler = Callable[[EventType, Any], Awaitable[None]]


class EventBus:
    def __init__(self) -> None:
        # Map: EventType → list of async handlers
        self._listeners: dict[EventType, list[Handler]] = defaultdict(list)
        # Serialise event delivery so the state machine sees events in order
        self._queue: asyncio.Queue[tuple[EventType, Any]] = asyncio.Queue()
        self._running = False

    # ------------------------------------------------------------------
    # Registration
    # ------------------------------------------------------------------

    def subscribe(self, event_type: EventType, handler: Handler) -> None:
        """Register an async handler for an event type."""
        self._listeners[event_type].append(handler)
        logger.debug("Subscribed %s → %s", event_type, handler.__qualname__)

    # ------------------------------------------------------------------
    # Emission
    # ------------------------------------------------------------------

    async def emit(self, event_type: EventType, data: Any = None) -> None:
        """
        Enqueue an event for delivery.
        Returns immediately — delivery happens in the dispatch loop.
        """
        logger.debug("Queued event %s | data=%s", event_type, data)
        await self._queue.put((event_type, data))

    # ------------------------------------------------------------------
    # Dispatch loop (run as a background task)
    # ------------------------------------------------------------------

    async def start(self) -> None:
        """Run the dispatch loop until stop() is called."""
        self._running = True
        logger.info("EventBus started")
        while self._running:
            try:
                event_type, data = await asyncio.wait_for(
                    self._queue.get(), timeout=1.0
                )
            except asyncio.TimeoutError:
                continue

            await self._dispatch(event_type, data)
            self._queue.task_done()

    async def _dispatch(self, event_type: EventType, data: Any) -> None:
        handlers = self._listeners.get(event_type, [])
        if not handlers:
            logger.debug("No handlers for %s", event_type)
            return

        for handler in handlers:
            try:
                await handler(event_type, data)
            except Exception:
                logger.exception(
                    "Handler %s raised for event %s", handler.__qualname__, event_type
                )

    async def stop(self) -> None:
        self._running = False
        logger.info("EventBus stopped")

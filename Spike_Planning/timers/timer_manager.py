"""
timer_manager.py — Async timer management.

The state machine never touches timers directly.
Flow:
  State machine emits START_TIMER  → TimerManager starts asyncio timer
  asyncio.sleep finishes           → TimerManager emits TIMEOUT via bus
  State machine emits CANCEL_TIMER → TimerManager cancels running task

Supports named timers so we can cancel a specific one (e.g. "planting")
without affecting others.
"""

import asyncio
import logging
from typing import Any

from events.event_bus import EventBus
from events.event_types import EventType

logger = logging.getLogger(__name__)


class TimerManager:
    def __init__(self, bus: EventBus) -> None:
        self._bus = bus
        # name → asyncio.Task
        self._timers: dict[str, asyncio.Task] = {}

    # ------------------------------------------------------------------
    # Event handlers (subscribed in main.py)
    # ------------------------------------------------------------------

    async def on_start_timer(self, _event_type: EventType, data: Any) -> None:
        """
        Handler for START_TIMER events.
        data = {"name": TimerName, "duration": int (seconds)}
        """
        name: str = data["name"]
        duration: int = data["duration"]

        # Cancel any existing timer with the same name (idempotent)
        await self._cancel(name)

        task = asyncio.create_task(
            self._run_timer(name, duration), name=f"timer:{name}"
        )
        self._timers[name] = task
        logger.info("Timer started: %s (%ds)", name, duration)

    async def on_cancel_timer(self, _event_type: EventType, data: Any) -> None:
        """
        Handler for CANCEL_TIMER events.
        data = {"name": TimerName | "all"}
        """
        name: str = data["name"]
        if name == "all":
            for n in list(self._timers.keys()):
                await self._cancel(n)
        else:
            await self._cancel(name)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    async def _run_timer(self, name: str, duration: int) -> None:
        try:
            await asyncio.sleep(duration)
            logger.info("Timer expired: %s", name)
            # Emit TIMEOUT — state machine will receive and transition
            await self._bus.emit(EventType.TIMEOUT, {"timer": name})
        except asyncio.CancelledError:
            logger.info("Timer cancelled: %s", name)

    async def _cancel(self, name: str) -> None:
        task = self._timers.pop(name, None)
        if task and not task.done():
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass

    def active_timers(self) -> list[str]:
        return [n for n, t in self._timers.items() if not t.done()]

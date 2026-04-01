"""
main.py — FastAPI entry point.

Startup order:
  1. Create EventBus, StateMachine, TimerManager, MQTTClient, WebSocketManager
  2. Wire all subscriptions (who listens to what)
  3. Start EventBus dispatch loop
  4. Start MQTT client
  5. Kick off with initial RESET → state machine goes to IDLE + starts main timer

Shutdown:
  Cancel all background tasks cleanly.

HTTP endpoints:
  GET  /status          → current state + active timers
  POST /event           → inject an event manually (for testing)
  WS   /ws              → real-time state stream

Event flow (example):
  MQTT pi/events/usb {action:inserted}
    → EventBus emits USB_INSERTED
    → state_machine_handler receives it
    → StateMachine returns TransitionResult
    → handler emits STATE_CHANGED + START_TIMER
    → WebSocketManager broadcasts state
    → TimerManager starts 60s countdown
"""

import asyncio
import logging
from contextlib import asynccontextmanager
from typing import Any
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import JSONResponse

from config import settings
from core.state_machine import SpikePlantingStateMachine
from events.event_bus import EventBus
from events.event_types import EventType
from iobridge.mqtt_client import MQTTClient
from iobridge.websocket_manager import WebSocketManager
from timers.timer_manager import TimerManager

logging.basicConfig(
    level=settings.log_level,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Module instances (singletons for this process)
# ---------------------------------------------------------------------------

bus = EventBus()
sm = SpikePlantingStateMachine()
timer_manager = TimerManager(bus)
mqtt_client = MQTTClient(bus)
ws_manager = WebSocketManager()


# ---------------------------------------------------------------------------
# State machine bridge
# ---------------------------------------------------------------------------

async def state_machine_handler(event_type: EventType, data: Any) -> None:
    """
    Central bridge: receives an inbound event, runs it through the state machine,
    and emits every resulting event back onto the bus.

    This is the ONLY place the state machine is called.
    """
    result = sm.process_event(event_type, data)
    if result is None:
        return  # event ignored — invalid in current state

    for emitted in result.events:
        await bus.emit(emitted.type, emitted.data)


# ---------------------------------------------------------------------------
# Subscription wiring
# ---------------------------------------------------------------------------

def wire_subscriptions() -> None:
    """
    Declare who listens to what.
    Order matters only for same-event same-module cases; generally irrelevant.
    """

    # --- Inbound hardware events → state machine ---
    bus.subscribe(EventType.USB_INSERTED, state_machine_handler)
    bus.subscribe(EventType.USB_REMOVED,  state_machine_handler)
    bus.subscribe(EventType.TIMEOUT,      state_machine_handler)
    bus.subscribe(EventType.RESET,        state_machine_handler)

    # --- Timer lifecycle → timer manager ---
    bus.subscribe(EventType.START_TIMER,  timer_manager.on_start_timer)
    bus.subscribe(EventType.CANCEL_TIMER, timer_manager.on_cancel_timer)

    # --- State changes → WebSocket broadcast ---
    bus.subscribe(EventType.STATE_CHANGED, ws_manager.on_state_changed)

    # --- State changes + output triggers → MQTT (back to Pi) ---
    bus.subscribe(EventType.STATE_CHANGED,  mqtt_client.on_state_changed)
    bus.subscribe(EventType.TRIGGER_OUTPUT, mqtt_client.on_trigger_output)

    logger.info("All subscriptions wired")


# ---------------------------------------------------------------------------
# FastAPI lifespan
# ---------------------------------------------------------------------------

_background_tasks: list[asyncio.Task] = []


@asynccontextmanager
async def lifespan(app: FastAPI):
    wire_subscriptions()

    # Start EventBus dispatch loop
    bus_task = asyncio.create_task(bus.start(), name="event_bus")
    _background_tasks.append(bus_task)

    # Start MQTT client (connects + listens in background)
    await mqtt_client.start()

    # Boot sequence: RESET → puts state machine in IDLE + starts main 10-min timer
    await bus.emit(EventType.RESET, {"reason": "startup"})

    logger.info("System ready")
    yield

    # --- Shutdown ---
    await mqtt_client.stop()
    await bus.stop()
    for task in _background_tasks:
        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            pass
    logger.info("Shutdown complete")


app = FastAPI(title="Spike Planting System", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# HTTP routes
# ---------------------------------------------------------------------------

@app.get("/status")
async def status():
    """Return current state and active timers."""
    return {
        "state": sm.state,
        "active_timers": timer_manager.active_timers(),
        "ws_clients": ws_manager.connection_count,
    }


@app.post("/event")
async def inject_event(body: dict):
    """
    Manually inject an event (for testing/debugging).

    Body:
        { "type": "USB_INSERTED" }
        { "type": "RESET" }
        { "type": "TIMEOUT", "data": {"timer": "planting"} }
    """
    try:
        event_type = EventType(body["type"])
    except (KeyError, ValueError) as exc:
        return JSONResponse(status_code=400, content={"error": str(exc)})

    await bus.emit(event_type, body.get("data"))
    return {"queued": event_type}


# ---------------------------------------------------------------------------
# WebSocket route
# ---------------------------------------------------------------------------

@app.websocket("/ws")
async def websocket_endpoint(ws: WebSocket):
    await ws_manager.connect(ws)
    try:
        while True:
            # Keep connection alive; clients are read-only (state is pushed)
            await ws.receive_text()
    except WebSocketDisconnect:
        ws_manager.disconnect(ws)


# ---------------------------------------------------------------------------
# Dev runner
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)

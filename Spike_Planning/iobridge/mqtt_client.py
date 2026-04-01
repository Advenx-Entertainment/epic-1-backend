"""
mqtt_client.py — MQTT ↔ EventBus bridge.

Responsibilities:
  • Subscribe to Raspberry Pi MQTT topics
  • Convert incoming MQTT messages → internal EventBus events
  • Listen for TRIGGER_OUTPUT events → publish GPIO commands back to Pi

Topics (inbound from Pi):
  pi/events/usb          → USB_INSERTED | USB_REMOVED
  pi/events/reset        → RESET

Topics (outbound to Pi):
  backend/state          → current state string
  pi/output/gpio         → action payload (spike_planted, defused, …)
"""

import asyncio
import json
import logging
from typing import Any

import asyncio_mqtt as amqtt

from config import settings
from events.event_bus import EventBus
from events.event_types import EventType

logger = logging.getLogger(__name__)


class MQTTClient:
    def __init__(self, bus: EventBus) -> None:
        self._bus = bus
        self._client: amqtt.Client | None = None
        self._running = False

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    async def start(self) -> None:
        """Connect and start listening in a background task."""
        self._running = True
        asyncio.create_task(self._listen_loop(), name="mqtt:listen")
        logger.info("MQTT client started (broker=%s:%d)", settings.mqtt_host, settings.mqtt_port)

    async def stop(self) -> None:
        self._running = False
        logger.info("MQTT client stopped")

    # ------------------------------------------------------------------
    # Inbound: MQTT → EventBus
    # ------------------------------------------------------------------

    async def _listen_loop(self) -> None:
        while self._running:
            try:
                async with amqtt.Client(
                    hostname=settings.mqtt_host,
                    port=settings.mqtt_port,
                ) as client:
                    self._client = client
                    async with client.messages() as messages:
                        await client.subscribe("pi/events/#")
                        logger.info("MQTT subscribed to pi/events/#")
                        async for message in messages:
                            await self._handle_message(
                                str(message.topic), message.payload.decode()
                            )
            except Exception:
                logger.exception("MQTT connection error — retrying in 5s")
                await asyncio.sleep(5)

    async def _handle_message(self, topic: str, payload: str) -> None:
        logger.debug("MQTT in: %s → %s", topic, payload)
        try:
            data = json.loads(payload) if payload else {}
        except json.JSONDecodeError:
            data = {"raw": payload}

        # Map topic → internal event
        if topic == "pi/events/usb":
            action = data.get("action", "")
            if action == "inserted":
                await self._bus.emit(EventType.USB_INSERTED, data)
            elif action == "removed":
                await self._bus.emit(EventType.USB_REMOVED, data)
            else:
                logger.warning("Unknown USB action: %s", action)

        elif topic == "pi/events/reset":
            await self._bus.emit(EventType.RESET, data)

        else:
            logger.debug("Unhandled topic: %s", topic)

    # ------------------------------------------------------------------
    # Outbound: EventBus → MQTT
    # ------------------------------------------------------------------

    async def on_state_changed(self, _event_type: EventType, data: Any) -> None:
        """Publish new state to backend/state topic."""
        await self._publish("backend/state", {"state": str(data)})

    async def on_trigger_output(self, _event_type: EventType, data: Any) -> None:
        """Forward GPIO/output trigger to the Pi."""
        await self._publish("pi/output/gpio", data)

    async def _publish(self, topic: str, payload: dict) -> None:
        if self._client is None:
            logger.warning("MQTT not connected — cannot publish to %s", topic)
            return
        try:
            await self._client.publish(topic, json.dumps(payload))
            logger.debug("MQTT out: %s → %s", topic, payload)
        except Exception:
            logger.exception("Failed to publish to %s", topic)

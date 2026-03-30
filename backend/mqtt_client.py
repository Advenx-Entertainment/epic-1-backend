import asyncio
import json
import os
import socket
import time
from typing import Any, Awaitable, Callable, Dict, Optional

import paho.mqtt.client as mqtt

_client: Optional[mqtt.Client] = None
_loop: Optional[asyncio.AbstractEventLoop] = None
_on_event: Optional[Callable[[Dict[str, Any]], Awaitable[None]]] = None
_last_error: Optional[str] = None
_connected: bool = False
_last_attempt_ts: Optional[float] = None


def _set_error(msg: str) -> None:
    global _last_error
    _last_error = msg
    print(f"[mqtt] {msg}")


def _on_connect(client: mqtt.Client, userdata: Any, flags: Any, rc: int) -> None:
    global _connected, _last_error
    if rc != 0:
        _connected = False
        _set_error(f"connect failed rc={rc}")
        return
    _connected = True
    _last_error = None
    topic = os.getenv("MQTT_TOPIC", "pi/events")
    client.subscribe(topic)


def _on_disconnect(client: mqtt.Client, userdata: Any, rc: int) -> None:
    global _connected
    _connected = False
    if rc != 0:
        _set_error(f"disconnected rc={rc}, will retry")


def _on_message(client: mqtt.Client, userdata: Any, msg: mqtt.MQTTMessage) -> None:
    payload = msg.payload.decode("utf-8", errors="ignore")
    try:
        data = json.loads(payload)
    except json.JSONDecodeError:
        data = payload

    event = {
        "type": "pi:event",
        "topic": msg.topic,
        "data": data,
    }
    if _loop and _on_event:
        asyncio.run_coroutine_threadsafe(_on_event(event), _loop)


def _should_enable_mqtt() -> bool:
    enabled = os.getenv("MQTT_ENABLED", "auto").strip().lower()
    if enabled in ("0", "false", "off", "no"):
        _set_error("disabled via MQTT_ENABLED")
        return False
    if enabled == "auto":
        host = os.getenv("MQTT_HOST")
        if not host:
            _set_error("auto-disabled: MQTT_HOST not set")
            return False
    return True


def _probe_broker(host: str, port: int, timeout_s: float = 2.0) -> bool:
    try:
        with socket.create_connection((host, port), timeout=timeout_s):
            return True
    except OSError:
        return False


def start_mqtt(
    loop: asyncio.AbstractEventLoop,
    on_event: Callable[[Dict[str, Any]], Awaitable[None]],
) -> None:
    global _client, _loop, _on_event, _last_attempt_ts
    if _client is not None:
        return

    if not _should_enable_mqtt():
        return

    _loop = loop
    _on_event = on_event

    host = os.getenv("MQTT_HOST", "localhost")
    port = int(os.getenv("MQTT_PORT", "1883"))
    username = os.getenv("MQTT_USERNAME")
    password = os.getenv("MQTT_PASSWORD")
    client_id = os.getenv("MQTT_CLIENT_ID", "backend")
    required = os.getenv("MQTT_REQUIRED", "0") == "1"

    if required and not _probe_broker(host, port):
        raise RuntimeError(f"MQTT broker not reachable at {host}:{port}")

    _last_attempt_ts = time.time()

    _client = mqtt.Client(client_id=client_id, protocol=mqtt.MQTTv311)
    if username:
        _client.username_pw_set(username, password)

    _client.on_connect = _on_connect
    _client.on_disconnect = _on_disconnect
    _client.on_message = _on_message
    _client.reconnect_delay_set(min_delay=1, max_delay=30)

    _client.connect_async(host, port, keepalive=60)
    _client.loop_start()


def mqtt_status() -> Dict[str, Any]:
    host = os.getenv("MQTT_HOST", "localhost")
    port = int(os.getenv("MQTT_PORT", "1883"))
    return {
        "enabled": _should_enable_mqtt(),
        "connected": _connected,
        "host": host,
        "port": port,
        "last_error": _last_error,
        "last_attempt_ts": _last_attempt_ts,
    }


def stop_mqtt() -> None:
    global _client
    if _client is None:
        return
    _client.loop_stop()
    _client.disconnect()
    _client = None

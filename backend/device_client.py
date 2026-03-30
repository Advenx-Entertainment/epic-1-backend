import asyncio
import json
import websockets
from datetime import datetime, timezone

DEVICE_ID = "sakshi_pc"
SERVER_URL = "wss://postdoctoral-acorned-terrance.ngrok-free.dev/ws/sakshi_pc"

def execute_action(action: str) -> str:
    handlers = {
        "laser_trip": lambda: "Laser trip system activated.",
        "system_lock": lambda: "System locked.",
        "alert_all": lambda: "Alert broadcast triggered.",
        "shutdown": lambda: "Shutdown sequence initiated.",
        "ping": lambda: "Pong.",
        "reset": lambda: "System reset complete.",
    }
    handler = handlers.get(action)
    if handler:
        return handler()
    return f"Unknown action: {action}"

async def send_response(websocket, action: str, result: str, target: str):
    response = {
        "type": "response",
        "action": action,
        "status": "ok",
        "message": result,
        "target": target,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }
    await websocket.send(json.dumps(response))

async def run():
    print(f"[{DEVICE_ID}] Connecting to {SERVER_URL}")
    async with websockets.connect(SERVER_URL) as websocket:
        print(f"[{DEVICE_ID}] Connected.")
        async for raw in websocket:
            msg = json.loads(raw)
            msg_type = msg.get("type")

            if msg_type == "command":
                target = msg.get("target", "all")
                if target not in ("all", DEVICE_ID):
                    continue
                action = msg.get("action", "")
                print(f"[{DEVICE_ID}] Received command: {action}")
                result = execute_action(action)
                print(f"[{DEVICE_ID}] Executed: {result}")
                await send_response(websocket, action, result, "co-dashboard")

            elif msg_type == "status":
                event = msg.get("event")
                print(f"[{DEVICE_ID}] Status event: {event} | Devices: {msg.get('connected_devices', [])}")

if __name__ == "__main__":
    asyncio.run(run())

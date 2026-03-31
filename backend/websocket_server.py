from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import json
from datetime import datetime, timezone
from typing import Dict

app = FastAPI()

class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}

    async def connect(self, websocket: WebSocket, device_id: str):
        await websocket.accept()
        self.active_connections[device_id] = websocket
        await self.broadcast({
            "type": "status",
            "event": "device_connected",
            "device_id": device_id,
            "connected_devices": list(self.active_connections.keys()),
            "timestamp": datetime.now(timezone.utc).isoformat()
        })

    def disconnect(self, device_id: str):
        self.active_connections.pop(device_id, None)

    async def send_to_device(self, device_id: str, message: dict):
        ws = self.active_connections.get(device_id)
        if ws:
            await ws.send_text(json.dumps(message))

    async def broadcast(self, message: dict):
        disconnected = []
        for device_id, ws in self.active_connections.items():
            try:
                await ws.send_text(json.dumps(message))
            except Exception:
                disconnected.append(device_id)
        for device_id in disconnected:
            self.disconnect(device_id)

manager = ConnectionManager()

@app.websocket("/ws/{device_id}")
async def websocket_endpoint(websocket: WebSocket, device_id: str):
    await manager.connect(websocket, device_id)
    try:
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)
            message["from"] = device_id
            message["timestamp"] = datetime.now(timezone.utc).isoformat()

            target = message.get("target", "all")
            if target == "all":
                await manager.broadcast(message)
            else:
                await manager.send_to_device(target, message)
                await manager.send_to_device(device_id, message)
    except WebSocketDisconnect:
        manager.disconnect(device_id)
        await manager.broadcast({
            "type": "status",
            "event": "device_disconnected",
            "device_id": device_id,
            "connected_devices": list(manager.active_connections.keys()),
            "timestamp": datetime.now(timezone.utc).isoformat()
        })

app.mount("/", StaticFiles(directory="../frontend", html=True), name="static")

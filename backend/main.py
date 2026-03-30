import asyncio
import json
import os
from typing import Any, Dict, Set

from dotenv import load_dotenv
from fastapi import Depends, FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from auth import create_access_token, require_jwt, verify_token
from mqtt_client import mqtt_status, start_mqtt, stop_mqtt

load_dotenv()

app = FastAPI(title="Pi <-> Backend <-> PC")

# Allow PC clients to connect from browser UIs
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class ConnectionManager:
    def __init__(self) -> None:
        self._connections: Set[WebSocket] = set()

    async def connect(self, websocket: WebSocket) -> None:
        await websocket.accept()
        self._connections.add(websocket)

    def disconnect(self, websocket: WebSocket) -> None:
        self._connections.discard(websocket)

    async def broadcast(self, message: Dict[str, Any]) -> None:
        if not self._connections:
            return
        payload = json.dumps(message)
        dead: Set[WebSocket] = set()
        for ws in self._connections:
            try:
                await ws.send_text(payload)
            except Exception:
                dead.add(ws)
        for ws in dead:
            self.disconnect(ws)


manager = ConnectionManager()


class LoginRequest(BaseModel):
    username: str
    password: str


@app.on_event("startup")
async def on_startup() -> None:
    loop = asyncio.get_running_loop()

    async def handle_event(event: Dict[str, Any]) -> None:
        await manager.broadcast(event)

    start_mqtt(loop=loop, on_event=handle_event)


@app.on_event("shutdown")
async def on_shutdown() -> None:
    stop_mqtt()


@app.post("/api/token")
async def issue_token(payload: LoginRequest) -> Dict[str, Any]:
    user = os.getenv("AUTH_USER", "admin")
    pwd = os.getenv("AUTH_PASS", "admin")
    if payload.username != user or payload.password != pwd:
        return {"ok": False, "error": "invalid_credentials"}
    token = create_access_token(subject=payload.username)
    return {"ok": True, "access_token": token, "token_type": "bearer"}


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket) -> None:
    token = websocket.query_params.get("token")
    if not token:
        await websocket.close(code=4401)
        return
    try:
        verify_token(token)
    except Exception:
        await websocket.close(code=4401)
        return

    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            try:
                parsed = json.loads(data)
                event = parsed if isinstance(parsed, dict) else {"type": "pc:message", "data": parsed}
            except json.JSONDecodeError:
                event = {"type": "pc:message", "data": data}
            await manager.broadcast(event)
    except WebSocketDisconnect:
        manager.disconnect(websocket)


@app.get("/api/mqtt/status")
async def api_mqtt_status() -> Dict[str, Any]:
    return mqtt_status()

@app.post("/api/ready")
async def api_ready(_: Dict[str, Any] = Depends(require_jwt)) -> Dict[str, Any]:
    event = {"type": "game:start"}
    await manager.broadcast(event)
    return {"ok": True, "broadcast": event}

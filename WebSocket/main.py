from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import json
import time
import asyncio

load_dotenv()

app = FastAPI(title="Game Ready Backend")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Shared state ──────────────────────────────────────────────
ready_teams: set[str] = set()
connected_clients: list[WebSocket] = []


# ── broadcast() — Person 2 implementation ────────────────────
async def broadcast(payload: dict):
    """Send a JSON payload to every connected WebSocket client."""
    message = json.dumps(payload, default=str)
    disconnected = []
    for ws in connected_clients:
        try:
            await ws.send_text(message)
        except Exception:
            disconnected.append(ws)
    for ws in disconnected:
        if ws in connected_clients:
            connected_clients.remove(ws)


# ── Person 1: REST endpoints ──────────────────────────────────

@app.get("/health")
async def health():
    """Server liveness check."""
    return {"status": "ok"}


@app.get("/api/status")
async def status():
    """How many teams are currently ready."""
    return {
        "ready_count": len(ready_teams),
        "ready_teams": list(ready_teams),
        "waiting_for": max(0, 2 - len(ready_teams)),
    }


@app.post("/api/ready")
async def team_ready(team_id: str):
    """
    Mark a team as ready.
    Increments counter — when both teams ready, broadcasts game:start.
    """
    ready_teams.add(team_id)
    current_count = len(ready_teams)

    if current_count >= 2:
        await broadcast({
            "type": "game:start",
            "message": "Both teams ready — game is starting!",
            "teams": list(ready_teams),
            "timestamp": time.time(),
        })
        return {
            "status": "game_started",
            "ready_count": current_count,
            "teams": list(ready_teams),
        }

    return {
        "status": "waiting",
        "ready_count": current_count,
        "waiting_for": 2 - current_count,
        "message": f"{current_count}/2 teams ready",
    }


@app.post("/api/reset")
async def reset():
    """Reset ready state for a new round."""
    ready_teams.clear()
    await broadcast({"type": "game:reset", "message": "Game has been reset"})
    return {"status": "reset", "message": "Ready state cleared"}


# ── Person 2: WebSocket endpoint ──────────────────────────────

@app.websocket("/ws")
async def websocket_endpoint(ws: WebSocket):
    """
    Persistent WebSocket connection.
    Handles ping/pong for latency measurement.
    Receives game:start broadcast when both teams ready.
    """
    await ws.accept()
    connected_clients.append(ws)
    try:
        while True:
            data = await ws.receive_text()
            msg = json.loads(data)

            # Latency ping/pong — echo ts back immediately
            if msg.get("type") == "ping":
                await ws.send_text(json.dumps({
                    "type": "pong",
                    "ts": msg["ts"],
                    "server_ts": time.time() * 1000,
                }))

    except WebSocketDisconnect:
        if ws in connected_clients:
            connected_clients.remove(ws)


# ── Person 2: extra status endpoints ─────────────────────────

@app.get("/person2/health")
async def person2_health():
    """Person 2 health check."""
    return {"health": "ok"}


@app.get("/person2/status")
async def person2_status():
    """Person 2 status — shows connected WS client count."""
    return {
        "status": "running",
        "connected_clients": len(connected_clients),
    }


@app.get("/person2/ready")
async def person2_ready():
    """Person 2 ready check."""
    return {"status": "person2 ready"}

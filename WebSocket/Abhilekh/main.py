from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import json
import time

load_dotenv()

app = FastAPI(title="Game Ready Backend")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Shared state ──────────────────────────────────────────────
# Tracks which teams have pressed ready
ready_teams: set[str] = set()

# Active WebSocket connections — Person 2 will fill the handlers
connected_clients: list[WebSocket] = []


# ── broadcast() stub — Person 2 will implement this ──────────
async def broadcast(payload: dict):
    """
    Send a JSON payload to every connected WebSocket client.
    Person 2 owns the full implementation of this function.
    Agreed interface: accepts a dict, sends to all clients.
    """
    message = json.dumps(payload, default=str)
    for ws in connected_clients:
        try:
            await ws.send_text(message)
        except Exception:
            pass  # Person 2 will add proper disconnect handling


# ── Person 1 owns everything below ───────────────────────────

@app.get("/health")
async def health():
    """Quick check to confirm the server is running."""
    return {"status": "ok"}


@app.get("/api/status")
async def status():
    """See how many teams are currently ready."""
    return {
        "ready_count": len(ready_teams),
        "ready_teams": list(ready_teams),
        "waiting_for": max(0, 2 - len(ready_teams)),
    }


@app.post("/api/ready")
async def team_ready(team_id: str):
    """
    Mark a team as ready.
    - Adds team_id to the ready set (set prevents duplicates)
    - When count reaches 2, broadcasts game:start to all WS clients
    - Returns current status
    """
    ready_teams.add(team_id)
    current_count = len(ready_teams)

    if current_count >= 2:
        await broadcast({
            "type": "game:start",
            "message": "Both teams ready - game is starting!",
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


# ── WebSocket endpoint stub — Person 2 owns this ─────────────
@app.websocket("/ws")
async def websocket_endpoint(ws: WebSocket):
    """
    Person 2 owns the full implementation.
    This stub keeps connection alive so Person 1 can test broadcast().
    """
    await ws.accept()
    connected_clients.append(ws)
    try:
        while True:
            await ws.receive_text()
    except WebSocketDisconnect:
        connected_clients.remove(ws)

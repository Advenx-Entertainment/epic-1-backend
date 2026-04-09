import json
import time
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

class ConnectionManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []
    
    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        print(f"[CONNECT] Total: {len(self.active_connections)}")
    
    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
        print(f"[DISCONNECT] Total: {len(self.active_connections)}")
    
    async def broadcast(self, message: dict):
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except:
                pass

manager = ConnectionManager()
game_counter = {"ready_count": 0}

app = FastAPI(title="Advenxure WebSocket Server")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
async def health():
    return {"status": "healthy"}

@app.get("/")
async def root():
    return {"message": "Advenxure WebSocket Server is running"}

@app.post("/api/ready")
async def team_ready():
    game_counter["ready_count"] += 1
    count = game_counter["ready_count"]
    if count >= 2:
        await manager.broadcast({
            "type": "game:start",
            "message": "Both teams ready! Game starting now.",
            "timestamp": time.time() * 1000
        })
        game_counter["ready_count"] = 0
    return {"ready": True, "count": count, "game_start": count >= 2}

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            msg = json.loads(data)
            if msg.get('type') == 'ping':
                send_time = msg.get('timestamp', time.time() * 1000)
                latency = (time.time() * 1000) - send_time
                print(f"[LATENCY] {latency:.2f} ms")
                await websocket.send_json({
                    "type": "pong",
                    "latency_ms": latency
                })
            else:
                print(f"[RECEIVED] {msg}")
    except WebSocketDisconnect:
        manager.disconnect(websocket)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
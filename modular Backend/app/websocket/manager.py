from fastapi import WebSocket
from typing import Dict, List


class WebSocketManager:
    def __init__(self):
        self.active_connections: Dict[str, List[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, room_id: str = "global") -> None:
        await websocket.accept()
        if room_id not in self.active_connections:
            self.active_connections[room_id] = []
        self.active_connections[room_id].append(websocket)

    def disconnect(self, websocket: WebSocket, room_id: str = "global") -> None:
        if room_id in self.active_connections:
            try:
                self.active_connections[room_id].remove(websocket)
            except ValueError:
                pass
            if not self.active_connections[room_id]:
                del self.active_connections[room_id]

    async def broadcast_all(self, message: dict, room_id: str = "global") -> None:
        if room_id not in self.active_connections:
            return
        dead: List[WebSocket] = []
        for connection in self.active_connections[room_id]:
            try:
                await connection.send_json(message)
            except Exception:
                dead.append(connection)
        for connection in dead:
            self.disconnect(connection, room_id)

    async def send_personal(self, message: dict, websocket: WebSocket) -> None:
        try:
            await websocket.send_json(message)
        except Exception:
            for room_id, connections in list(self.active_connections.items()):
                if websocket in connections:
                    self.disconnect(websocket, room_id)
                    break

    def get_connection_count(self, room_id: str = "global") -> int:
        if room_id == "global":
            return sum(len(conns) for conns in self.active_connections.values())
        return len(self.active_connections.get(room_id, []))


websocket_manager = WebSocketManager()

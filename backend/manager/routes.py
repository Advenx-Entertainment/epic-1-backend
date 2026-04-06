from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from manager.webso import manager

router = APIRouter()

@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)

    # READY signal send hoga connect hote hi
    await manager.send_personal("READY", websocket)

    try:
        while True:
            data = await websocket.receive_text()
            print("Received:", data)
            await manager.send_personal(f"Echo: {data}", websocket)

    except WebSocketDisconnect:
        manager.disconnect(websocket)
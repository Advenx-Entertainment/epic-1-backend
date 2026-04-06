from fastapi import FastAPI
from app.websocket.routes import router as ws_router

app = FastAPI()

app.include_router(ws_router)

@app.get("/")
def health():
    return {"status": "Server running"}
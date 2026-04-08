from pydantic import BaseModel, Field
from typing import Any, Optional
from datetime import datetime


class HealthResponse(BaseModel):
    status: str
    websocket_connections: int
    app_name: str
    environment: str


class WSMessage(BaseModel):
    event: str
    payload: Any = None
    room_id: str = "global"
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class WSAck(BaseModel):
    success: bool
    event: str
    message: Optional[str] = None


class ErrorResponse(BaseModel):
    error: str
    detail: Optional[str] = None
    status_code: int

from typing import Any, Optional

from pydantic import BaseModel


class Event(BaseModel):
    type: str
    data: Any
    topic: Optional[str] = None

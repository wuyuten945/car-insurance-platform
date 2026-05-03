from pydantic import BaseModel
from datetime import datetime


class ChatMessageSend(BaseModel):
    content: str


class ChatMessageOut(BaseModel):
    id: str
    sender: str  # user, bot, agent
    content: str
    intent: str | None = None
    confidence: float | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


class ChatSessionOut(BaseModel):
    id: str
    status: str
    started_at: datetime
    ended_at: datetime | None = None
    messages: list[ChatMessageOut] = []

    model_config = {"from_attributes": True}

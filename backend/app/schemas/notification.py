from pydantic import BaseModel
from datetime import datetime


class NotificationOut(BaseModel):
    id: str
    title: str
    body: str
    notification_type: str
    reference_type: str | None = None
    reference_id: str | None = None
    is_read: bool
    sent_at: datetime | None = None
    created_at: datetime

    model_config = {"from_attributes": True}

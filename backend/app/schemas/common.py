from pydantic import BaseModel
from typing import Any
from datetime import datetime


class APIResponse(BaseModel):
    success: bool = True
    data: Any = None
    message: str = "操作成功"
    timestamp: datetime = None
    request_id: str | None = None

    def model_post_init(self, __context):
        if self.timestamp is None:
            from datetime import timezone
            self.timestamp = datetime.now(timezone.utc)


class PaginatedResponse(BaseModel):
    items: list[Any]
    total: int
    page: int
    per_page: int
    pages: int

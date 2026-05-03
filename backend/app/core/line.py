import logging
import httpx

from app.config import settings

logger = logging.getLogger(__name__)


class MockLINEService:
    """開發用 Mock LINE Notify，只印到 console。"""

    async def send(self, user_id: str, message: str) -> bool:
        logger.info(f"[LINE Mock] To user: {user_id} | Message: {message}")
        print(f"[LINE Mock] To user: {user_id} | Message: {message[:80]}")
        return True


class LINENotifyService:
    """
    LINE Notify 正式服務。
    需設定環境變數 LINE_CHANNEL_ACCESS_TOKEN。
    生產環境將 Mock 替換為此類別。
    """

    def __init__(self):
        self.api_url = "https://api.line.me/v2/bot/message/push"
        self.token = getattr(settings, "LINE_CHANNEL_ACCESS_TOKEN", "")

    async def send(self, user_id: str, message: str) -> bool:
        if not self.token:
            logger.warning("[LINE] 未設定 LINE_CHANNEL_ACCESS_TOKEN，略過發送")
            return False

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.token}",
        }
        payload = {
            "to": user_id,
            "messages": [{"type": "text", "text": message}],
        }
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.post(self.api_url, json=payload, headers=headers)
                resp.raise_for_status()
            logger.info(f"[LINE] 發送成功: {user_id}")
            return True
        except Exception as e:
            logger.error(f"[LINE] 發送失敗: {e}")
            return False


# 根據設定選擇實例
if getattr(settings, "LINE_CHANNEL_ACCESS_TOKEN", ""):
    line_service = LINENotifyService()
else:
    line_service = MockLINEService()

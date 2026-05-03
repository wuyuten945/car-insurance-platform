import logging

logger = logging.getLogger(__name__)


class MockPushService:
    """開發用 Mock 推播，只印到 console。生產環境替換為 FCM/APNs。"""

    async def send(self, user_id: str, title: str, body: str, data: dict = None) -> bool:
        logger.info(f"[Push Mock] To user: {user_id} | Title: {title}")
        return True


push_service = MockPushService()

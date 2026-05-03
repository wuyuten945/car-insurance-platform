import logging

logger = logging.getLogger(__name__)


class MockSMSGateway:
    """開發用 Mock SMS，只印到 console。生產環境替換為真實 SMS 服務。"""

    async def send(self, phone: str, message: str) -> bool:
        logger.info(f"[SMS Mock] To: {phone} | Message: {message}")
        print(f"[SMS Mock] To: {phone} | Message: {message[:80]}")
        return True


sms_gateway = MockSMSGateway()

import logging
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from app.config import settings

logger = logging.getLogger(__name__)


class MockEmailService:
    """開發用 Mock Email，只印到 console。"""

    async def send(self, to_email: str, subject: str, body: str) -> bool:
        logger.info(f"[Email Mock] To: {to_email} | Subject: {subject}")
        print(f"[Email Mock] To: {to_email} | Subject: {subject}")
        return True


class SMTPEmailService:
    """
    SMTP 正式郵件服務。
    需設定環境變數 SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASSWORD, SMTP_FROM。
    """

    def __init__(self):
        self.host = getattr(settings, "SMTP_HOST", "")
        self.port = getattr(settings, "SMTP_PORT", 587)
        self.user = getattr(settings, "SMTP_USER", "")
        self.password = getattr(settings, "SMTP_PASSWORD", "")
        self.from_addr = getattr(settings, "SMTP_FROM", "noreply@car-insurance.com")

    async def send(self, to_email: str, subject: str, body: str) -> bool:
        if not self.host or not self.user:
            logger.warning("[Email] 未設定 SMTP 參數，略過發送")
            return False

        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = self.from_addr
        msg["To"] = to_email
        msg.attach(MIMEText(body, "html", "utf-8"))

        try:
            with smtplib.SMTP(self.host, self.port) as server:
                server.starttls()
                server.login(self.user, self.password)
                server.sendmail(self.from_addr, to_email, msg.as_string())
            logger.info(f"[Email] 發送成功: {to_email}")
            return True
        except Exception as e:
            logger.error(f"[Email] 發送失敗: {e}")
            return False


# 根據設定選擇實例
if getattr(settings, "SMTP_HOST", ""):
    email_service = SMTPEmailService()
else:
    email_service = MockEmailService()

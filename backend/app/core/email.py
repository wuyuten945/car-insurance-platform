import logging
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

import httpx

from app.config import settings

logger = logging.getLogger(__name__)


class MockEmailService:
    """開發用 Mock Email，只印到 console。"""

    async def send(self, to_email: str, subject: str, body: str) -> bool:
        logger.info(f"[Email Mock] To: {to_email} | Subject: {subject}")
        print(f"[Email Mock] To: {to_email} | Subject: {subject}")
        return True


class ResendEmailService:
    """
    Resend HTTP API 寄信（用於 Render Free 等擋 SMTP 的環境）。
    需設定 RESEND_API_KEY；from 位址預設用 sandbox（onboarding@resend.dev），
    正式上線請綁網域並改 RESEND_FROM。
    """

    def __init__(self):
        self.api_key = getattr(settings, "RESEND_API_KEY", "")
        self.from_addr = getattr(settings, "RESEND_FROM", "onboarding@resend.dev")

    async def send(self, to_email: str, subject: str, body: str) -> bool:
        if not self.api_key:
            logger.warning("[Email] 未設定 RESEND_API_KEY，略過發送")
            return False
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                resp = await client.post(
                    "https://api.resend.com/emails",
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json",
                    },
                    json={
                        "from": self.from_addr,
                        "to": [to_email],
                        "subject": subject,
                        "html": body,
                    },
                )
            if resp.status_code in (200, 202):
                logger.info(f"[Email/Resend] 發送成功: {to_email}")
                return True
            logger.error(f"[Email/Resend] 失敗 {resp.status_code}: {resp.text}")
            return False
        except Exception as e:
            logger.error(f"[Email/Resend] 例外: {e}")
            return False


class SMTPEmailService:
    """
    SMTP 正式郵件服務。
    需設定環境變數 SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASSWORD, SMTP_FROM。
    注意：Render Free 層擋 SMTP，需付費或改用 Resend。
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


# 服務優先順序：Resend > SMTP > Mock
if getattr(settings, "RESEND_API_KEY", ""):
    email_service = ResendEmailService()
elif getattr(settings, "SMTP_HOST", ""):
    email_service = SMTPEmailService()
else:
    email_service = MockEmailService()

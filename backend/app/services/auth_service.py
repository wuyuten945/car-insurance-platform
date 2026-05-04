from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.user import User
from app.core.security import (
    create_otp, store_otp, verify_otp, check_otp_rate_limit,
    create_access_token, create_refresh_token, decode_token, blacklist_token,
)
from app.core.email import email_service
from app.config import settings
from app.exceptions import BadRequestError, UnauthorizedError, RateLimitError


class AuthService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def send_otp(self, email: str, ip: str = "") -> dict:
        """發送 Email OTP。手機 OTP 已停用以避免 SMS 簡訊費用被惡意刷取。"""
        if not email:
            raise BadRequestError("請提供 Email")

        # per-email rate limit
        if not await check_otp_rate_limit(f"email:{email}"):
            raise RateLimitError("OTP 發送過於頻繁，請稍後再試")

        # per-IP rate limit（防止攻擊者輪流換 email 大量觸發）
        if ip and not await check_otp_rate_limit(f"ip:{ip}", per_minute=5, per_hour=50):
            raise RateLimitError("此 IP 發送驗證碼過於頻繁，請稍後再試")

        otp = create_otp()
        await store_otp(email, otp)

        await email_service.send(
            email,
            "【BOPINAN】登入驗證碼",
            f"<p>您的驗證碼為 <b style='font-size:24px;letter-spacing:4px'>{otp}</b></p>"
            f"<p>{settings.OTP_EXPIRE_SECONDS // 60} 分鐘內有效，請勿將驗證碼提供給他人。</p>",
        )

        return {"message": "驗證碼已發送", "expires_in": settings.OTP_EXPIRE_SECONDS, "method": "email"}

    async def verify_otp_and_login(self, email: str, otp: str) -> dict:
        if not email:
            raise BadRequestError("請提供 Email")

        if not await verify_otp(email, otp):
            raise BadRequestError("驗證碼錯誤或已過期")

        result = await self.db.execute(select(User).where(User.email == email))
        user = result.scalar_one_or_none()

        if not user:
            user = User(email=email)
            self.db.add(user)
            await self.db.flush()

        user.last_login_at = datetime.now(timezone.utc)

        access_token = create_access_token(user.id)
        refresh_token = create_refresh_token(user.id)

        return {
            "user": user,
            "access_token": access_token,
            "refresh_token": refresh_token,
            "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        }

    async def refresh_tokens(self, refresh_token: str) -> dict:
        payload = decode_token(refresh_token)
        if not payload or payload.get("type") != "refresh":
            raise UnauthorizedError("無效的 Refresh Token")

        user_id = payload.get("sub")
        result = await self.db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()

        if not user or not user.is_active:
            raise UnauthorizedError("使用者不存在或已停用")

        new_access = create_access_token(user.id)
        new_refresh = create_refresh_token(user.id)

        return {
            "access_token": new_access,
            "refresh_token": new_refresh,
            "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        }

    async def logout(self, token: str) -> None:
        await blacklist_token(token)

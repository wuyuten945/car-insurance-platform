import time
import hashlib
import secrets
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from jose import jwt
from app.models.user import User
from app.core.security import (
    create_otp, store_otp, verify_otp, check_otp_rate_limit,
    create_access_token, create_refresh_token, decode_token, blacklist_token,
)
from app.core.email import email_service
from app.core.i18n import t
from app.config import settings
from app.exceptions import BadRequestError, UnauthorizedError, RateLimitError


# ── 二因子保護密碼 helpers ─────────────────────────────
INTERIM_TOKEN_TTL = 300  # 5 分鐘短效，OTP 通過後等用戶輸密碼用


def _hash_password(plain: str) -> str:
    """使用 bcrypt(成本 12)。新雜湊格式以 '$2b$' 開頭。

    舊 SHA-256 雜湊 'salt$digest' 仍可用 _verify_password 驗證,但下次密碼變更會自動升級。
    """
    from passlib.hash import bcrypt
    return bcrypt.using(rounds=12).hash(plain)


def _verify_password(plain: str, stored: str) -> bool:
    if not stored:
        return False
    # bcrypt 雜湊
    if stored.startswith("$2"):
        try:
            from passlib.hash import bcrypt
            return bcrypt.verify(plain, stored)
        except Exception:
            return False
    # 舊 SHA-256 + salt 格式 (向下相容)
    if "$" in stored:
        salt, digest = stored.split("$", 1)
        expected = hashlib.sha256((salt + plain).encode("utf-8")).hexdigest()
        return secrets.compare_digest(expected, digest)
    return False


def needs_rehash(stored: str) -> bool:
    """舊 SHA-256 雜湊應在下次驗證成功時自動重 hash 為 bcrypt"""
    return bool(stored) and not stored.startswith("$2")


def _create_interim_token(user_id: str) -> str:
    """OTP 通過後發短效 interim_token，僅供 verify-password 使用"""
    return jwt.encode({
        "sub": user_id,
        "type": "otp_pending",
        "exp": int(time.time()) + INTERIM_TOKEN_TTL,
    }, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def _decode_interim_token(token: str) -> str | None:
    try:
        payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
        if payload.get("type") != "otp_pending":
            return None
        return payload.get("sub")
    except Exception:
        return None


class AuthService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def send_otp(self, email: str, ip: str = "") -> dict:
        """發送 Email OTP。手機 OTP 已停用以避免 SMS 簡訊費用被惡意刷取。"""
        if not email:
            raise BadRequestError(t("email_required"))

        # per-email rate limit
        if not await check_otp_rate_limit(f"email:{email}"):
            raise RateLimitError(t("otp_rate_email"))

        # per-IP rate limit（防止攻擊者輪流換 email 大量觸發）
        if ip and not await check_otp_rate_limit(f"ip:{ip}", per_minute=5, per_hour=50):
            raise RateLimitError(t("otp_rate_ip"))

        otp = create_otp()
        await store_otp(email, otp)

        await email_service.send(
            email,
            "【BOPINAN】登入驗證碼",
            f"<p>您的驗證碼為 <b style='font-size:24px;letter-spacing:4px'>{otp}</b></p>"
            f"<p>{settings.OTP_EXPIRE_SECONDS // 60} 分鐘內有效，請勿將驗證碼提供給他人。</p>",
        )

        return {"message": t("otp_sent"), "expires_in": settings.OTP_EXPIRE_SECONDS, "method": "email"}

    async def verify_otp_and_login(self, email: str, otp: str) -> dict:
        if not email:
            raise BadRequestError(t("email_required"))

        if not await verify_otp(email, otp):
            raise BadRequestError(t("otp_invalid"))

        result = await self.db.execute(select(User).where(User.email == email))
        user = result.scalar_one_or_none()

        if not user:
            user = User(email=email)
            self.db.add(user)
            await self.db.flush()

        # ★ 雙因子：若有 password_hash → 不直接發 token，發 interim_token 讓前端再要密碼
        if user.password_hash:
            interim = _create_interim_token(user.id)
            return {
                "step": "password_required",
                "interim_token": interim,
                "expires_in": INTERIM_TOKEN_TTL,
            }

        user.last_login_at = datetime.now(timezone.utc)
        access_token = create_access_token(user.id)
        refresh_token = create_refresh_token(user.id)

        return {
            "step": "logged_in",
            "user": user,
            "access_token": access_token,
            "refresh_token": refresh_token,
            "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        }

    async def verify_password_with_interim(self, interim_token: str, password: str) -> dict:
        """OTP 通過後的二因子驗證：用 interim_token + 密碼換正式 tokens

        安全:interim_token 用過即 blacklist,防 replay。
        """
        user_id = _decode_interim_token(interim_token)
        if not user_id:
            raise UnauthorizedError(t("pw_session_expired"))

        # 一旦 decode 成功就先 blacklist,避免下面任一驗證失敗時 token 仍可被用
        from app.core.security import blacklist_token, is_token_blacklisted
        if await is_token_blacklisted(interim_token):
            raise UnauthorizedError(t("pw_session_expired"))
        await blacklist_token(interim_token)

        result = await self.db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
        if not user or not user.is_active:
            raise UnauthorizedError(t("user_not_active"))
        if not user.password_hash:
            raise BadRequestError(t("pw_not_enabled"))
        if not _verify_password(password, user.password_hash):
            raise BadRequestError(t("pw_wrong"))

        # 透明升級舊 SHA-256 雜湊為 bcrypt(只在驗證成功後執行)
        if needs_rehash(user.password_hash):
            user.password_hash = _hash_password(password)

        user.last_login_at = datetime.now(timezone.utc)
        access_token = create_access_token(user.id)
        refresh_token = create_refresh_token(user.id)
        return {
            "step": "logged_in",
            "user": user,
            "access_token": access_token,
            "refresh_token": refresh_token,
            "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        }

    async def set_advanced_password(self, user_id: str, new_password: str,
                                     current_password: str | None) -> None:
        """
        設定/變更進階保護密碼。
        - 第一次設定（user.password_hash is None）：不需 current_password
        - 已有密碼 → 必須提供正確 current_password 才能改（防止 token 被盜直接改）
        """
        result = await self.db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
        if not user:
            raise UnauthorizedError(t("user_not_found"))
        if user.password_hash:
            if not current_password or not _verify_password(current_password, user.password_hash):
                raise BadRequestError(t("pw_current_wrong"))
            if new_password == current_password:
                raise BadRequestError(t("pw_same_as_current"))
        user.password_hash = _hash_password(new_password)
        await self.db.flush()

    async def remove_advanced_password(self, user_id: str, current_password: str) -> None:
        """移除進階保護密碼（須驗證當前密碼）"""
        result = await self.db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
        if not user:
            raise UnauthorizedError(t("user_not_found"))
        if not user.password_hash:
            raise BadRequestError(t("pw_not_enabled"))
        if not _verify_password(current_password, user.password_hash):
            raise BadRequestError(t("pw_current_wrong"))
        user.password_hash = None
        await self.db.flush()

    async def refresh_tokens(self, refresh_token: str) -> dict:
        payload = decode_token(refresh_token)
        if not payload or payload.get("type") != "refresh":
            raise UnauthorizedError(t("refresh_invalid"))

        user_id = payload.get("sub")
        result = await self.db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()

        if not user or not user.is_active:
            raise UnauthorizedError(t("user_not_active"))

        new_access = create_access_token(user.id)
        new_refresh = create_refresh_token(user.id)

        return {
            "access_token": new_access,
            "refresh_token": new_refresh,
            "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        }

    async def logout(self, token: str) -> None:
        await blacklist_token(token)

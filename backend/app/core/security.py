import random
import string
from datetime import datetime, timedelta, timezone
from jose import jwt, JWTError
from app.config import settings
from app.core.cache import cache


def create_otp(length: int = None) -> str:
    length = length or settings.OTP_LENGTH
    return "".join(random.choices(string.digits, k=length))


async def store_otp(phone: str, otp: str) -> None:
    key = f"otp:{phone}"
    await cache.set(key, otp, ttl=settings.OTP_EXPIRE_SECONDS)


async def verify_otp(phone: str, otp: str) -> bool:
    key = f"otp:{phone}"
    stored = await cache.get(key)
    if stored and stored == otp:
        await cache.delete(key)
        return True
    return False


async def check_otp_rate_limit(key: str, per_minute: int = 1, per_hour: int = 5) -> bool:
    """通用 OTP rate limit(已收緊以防止 OTP 枚舉攻擊)。

    key: 任意識別字串，e.g. "email:foo@bar.com" 或 "ip:1.2.3.4"
    per_minute: 10 秒視窗內允許次數（預設 1，符合「每 10 秒最多 1 次」原語意）
    per_hour: 每小時允許次數（預設 5,從 30 收緊。6 位數 OTP 1M 組合,5 次/hr 防爆破）
    """
    minute_key = f"otp_rate:min:{key}"
    hour_key = f"otp_rate:hour:{key}"

    minute_count = await cache.get(minute_key)
    if minute_count and minute_count >= per_minute:
        return False

    hour_count = await cache.get(hour_key)
    if hour_count and hour_count >= per_hour:
        return False

    await cache.increment(minute_key, ttl=10)
    await cache.increment(hour_key, ttl=3600)
    return True


def create_access_token(user_id: str, token_version: int = 0) -> str:
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    payload = {
        "sub": user_id,
        "exp": expire,
        "type": "access",
        "tv": int(token_version or 0),
    }
    return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def create_refresh_token(user_id: str, token_version: int = 0) -> str:
    expire = datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    payload = {
        "sub": user_id,
        "exp": expire,
        "type": "refresh",
        "tv": int(token_version or 0),
    }
    return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def decode_token(token: str) -> dict | None:
    try:
        payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
        return payload
    except JWTError:
        return None


async def blacklist_token(token: str, ttl: int = None) -> None:
    """將 token 加入黑名單（登出用）"""
    ttl = ttl or settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
    await cache.set(f"blacklist:{token}", True, ttl=ttl)


async def is_token_blacklisted(token: str) -> bool:
    return await cache.exists(f"blacklist:{token}")

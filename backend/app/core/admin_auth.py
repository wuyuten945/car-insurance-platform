"""
管理員認證 + 權限控制（獨立於客戶認證系統）
"""
import hashlib
import secrets
import logging
from datetime import datetime, timezone
from fastapi import Depends, Header, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_db
from app.models.admin_user import AdminUser, AgentCustomer, AuditLog
from app.core.security import create_access_token, decode_token
from app.exceptions import UnauthorizedError, ForbiddenError

logger = logging.getLogger(__name__)


def _bcrypt_hash(password: str) -> str:
    """直接用 bcrypt 套件,避開 passlib 與新版 bcrypt 的相容性問題。"""
    import bcrypt as _bc
    # bcrypt 上限 72 bytes(規格限制),超過會 silently 截斷,這裡明確截斷以一致行為
    pw_bytes = password.encode("utf-8")[:72]
    return _bc.hashpw(pw_bytes, _bc.gensalt(rounds=12)).decode("utf-8")


def _bcrypt_verify(password: str, hashed: str) -> bool:
    import bcrypt as _bc
    try:
        return _bc.checkpw(password.encode("utf-8")[:72], hashed.encode("utf-8"))
    except Exception:
        return False


def hash_password(password: str) -> str:
    """密碼加密 — 新格式用 bcrypt(成本 12, '$2b$' 開頭)。
    舊格式 'salt:digest' (SHA-256) 仍可被 verify_password 驗證以保持向下相容,
    並在使用者下次成功登入時透過 needs_rehash() 升級。
    """
    return _bcrypt_hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    """驗證密碼。同時相容 bcrypt(新)和舊 SHA-256+salt 格式。"""
    if not password_hash:
        return False
    if password_hash.startswith("$2"):
        return _bcrypt_verify(password, password_hash)
    if ":" in password_hash:
        salt, h = password_hash.split(":", 1)
        return hashlib.sha256((salt + password).encode()).hexdigest() == h
    return False


def needs_rehash(password_hash: str) -> bool:
    """舊 SHA-256 雜湊應在下次驗證成功時升級為 bcrypt"""
    return bool(password_hash) and not password_hash.startswith("$2")


def generate_api_key() -> str:
    """產生 64 字元 API Key"""
    return secrets.token_hex(32)


async def get_current_admin(
    authorization: str = Header(..., description="Bearer <token> or ApiKey <key>"),
    db: AsyncSession = Depends(get_db),
) -> AdminUser:
    """取得當前管理員（支援 JWT 和 API Key）"""

    from app.core.i18n import t as _t
    if authorization.startswith("Bearer "):
        token = authorization[7:]
        payload = decode_token(token)
        if not payload or payload.get("type") != "admin":
            raise UnauthorizedError(_t("token_invalid"))
        admin_id = payload.get("sub")
        result = await db.execute(select(AdminUser).where(AdminUser.id == admin_id))
        admin = result.scalar_one_or_none()
        # Token version 檢查:改密碼時 admin.token_version +1,舊 token 立刻失效
        if admin and int(payload.get("tv", 0)) != int(admin.token_version or 0):
            raise UnauthorizedError(_t("token_invalid"))

    elif authorization.startswith("ApiKey "):
        api_key = authorization[7:]
        result = await db.execute(select(AdminUser).where(AdminUser.api_key == api_key))
        admin = result.scalar_one_or_none()

    else:
        raise UnauthorizedError(_t("auth_invalid_header"))

    if not admin:
        raise UnauthorizedError(_t("admin_not_found"))
    if not admin.is_active:
        raise ForbiddenError(_t("admin_disabled"))

    return admin


def require_super_admin(admin: AdminUser = Depends(get_current_admin)) -> AdminUser:
    """要求超級管理員權限"""
    if admin.role != "super_admin":
        from app.core.i18n import t as _t
        raise ForbiddenError(_t("admin_super_required"))
    return admin


async def get_accessible_customer_ids(admin: AdminUser, db: AsyncSession) -> list[str] | None:
    """取得管理員可存取的客戶 ID 列表。super_admin 回傳 None（全部）"""
    if admin.role == "super_admin":
        return None  # 不限制
    result = await db.execute(
        select(AgentCustomer.customer_id).where(AgentCustomer.agent_id == admin.id)
    )
    return [row[0] for row in result.all()]


async def log_action(
    db: AsyncSession, admin: AdminUser, action: str,
    target_type: str = "", target_id: str = "",
    detail: str = "", ip: str = "",
):
    """記錄操作日誌"""
    db.add(AuditLog(
        admin_user_id=admin.id,
        action=action,
        target_type=target_type,
        target_id=target_id,
        detail=detail,
        ip_address=ip,
    ))

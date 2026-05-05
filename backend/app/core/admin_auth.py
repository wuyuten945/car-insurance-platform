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


def hash_password(password: str) -> str:
    """密碼加密（SHA-256 + salt）"""
    salt = secrets.token_hex(16)
    h = hashlib.sha256((salt + password).encode()).hexdigest()
    return f"{salt}:{h}"


def verify_password(password: str, password_hash: str) -> bool:
    """驗證密碼"""
    if ":" not in password_hash:
        return False
    salt, h = password_hash.split(":", 1)
    return hashlib.sha256((salt + password).encode()).hexdigest() == h


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

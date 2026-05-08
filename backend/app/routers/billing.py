"""
訂閱制 API — 詳見 SUBSCRIPTION_SPEC.md
"""
from __future__ import annotations

import logging
from dataclasses import asdict

from fastapi import APIRouter, Depends, Query, Request
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.admin_auth import get_current_admin, require_super_admin, log_action
from app.dependencies import get_db
from app.exceptions import BadRequestError, NotFoundError
from app.models.admin_user import AdminUser
from app.schemas.common import APIResponse
from app.services import subscription_service as svc

logger = logging.getLogger(__name__)
router = APIRouter()


# ─────────────────────────────────────────────────────────────
# 業務員自己 — 永遠可訪問(不被 require_active_subscription 擋)
# ─────────────────────────────────────────────────────────────


@router.get("/subscription/me", response_model=APIResponse)
async def get_my_subscription(admin: AdminUser = Depends(get_current_admin)):
    """看自己的訂閱狀態。"""
    return APIResponse(data=asdict(svc.to_view(admin)))


@router.post("/subscription/cancel", response_model=APIResponse)
async def cancel_my_subscription(
    admin: AdminUser = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """取消自己訂閱(用到當期結束才停)。"""
    if admin.role == "super_admin":
        raise BadRequestError("super_admin 無訂閱可取消")
    svc.cancel(admin)
    await log_action(db, admin, "subscription_cancel", "self", admin.id, "agent 自助取消訂閱")
    await db.flush()
    return APIResponse(data=asdict(svc.to_view(admin)), message="訂閱已取消,可使用至當期結束")


# ─────────────────────────────────────────────────────────────
# super_admin — 管理所有 agent 的訂閱
# ─────────────────────────────────────────────────────────────


@router.get("/subscriptions", response_model=APIResponse)
async def list_subscriptions(
    page: int = Query(1, ge=1),
    per_page: int = Query(100, ge=1, le=500),
    admin: AdminUser = Depends(require_super_admin),
    db: AsyncSession = Depends(get_db),
):
    """列出所有 agent 的訂閱狀態(僅 super_admin)。"""
    query = (
        select(AdminUser)
        .where(AdminUser.role == "agent")
        .order_by(AdminUser.created_at.desc())
        .offset((page - 1) * per_page)
        .limit(per_page)
    )
    result = await db.execute(query)
    rows = []
    for a in result.scalars().all():
        view = svc.to_view(a)
        rows.append({
            "agent_id": a.id,
            "username": a.username,
            "display_name": a.display_name,
            "is_active": a.is_active,
            **asdict(view),
        })
    return APIResponse(data=rows)


class ExtendRequest(BaseModel):
    # 限 1-60 個月,防 super_admin 手滑或 API 被濫用造成 740 年訂閱
    months: int = Field(1, ge=1, le=60)
    # 限長 100 字,對齊 DB 欄位,防超長字串或 binary blob
    payment_ref: str | None = Field(None, max_length=100)


@router.post("/subscriptions/{agent_id}/extend", response_model=APIResponse)
async def extend_subscription(
    agent_id: str,
    req: ExtendRequest,
    admin: AdminUser = Depends(require_super_admin),
    db: AsyncSession = Depends(get_db),
):
    """super_admin 手動延長 N 個月(收到匯款後標記)。"""
    result = await db.execute(select(AdminUser).where(AdminUser.id == agent_id))
    agent = result.scalar_one_or_none()
    if not agent:
        raise NotFoundError("業務員不存在")
    if agent.role == "super_admin":
        raise BadRequestError("super_admin 無訂閱可延長")
    svc.extend_paid(agent, months=req.months, payment_ref=req.payment_ref)
    await log_action(
        db, admin, "subscription_extend", "agent", agent.id,
        f"延長 {req.months} 個月,ref={req.payment_ref or '-'}",
    )
    await db.flush()
    return APIResponse(data=asdict(svc.to_view(agent)), message=f"已延長 {req.months} 個月")


@router.post("/subscriptions/{agent_id}/cancel", response_model=APIResponse)
async def admin_cancel_subscription(
    agent_id: str,
    admin: AdminUser = Depends(require_super_admin),
    db: AsyncSession = Depends(get_db),
):
    """super_admin 強制取消某 agent 訂閱(用到當期結束)。"""
    result = await db.execute(select(AdminUser).where(AdminUser.id == agent_id))
    agent = result.scalar_one_or_none()
    if not agent:
        raise NotFoundError("業務員不存在")
    if agent.role == "super_admin":
        raise BadRequestError("super_admin 無訂閱可取消")
    svc.cancel(agent)
    await log_action(db, admin, "subscription_cancel", "agent", agent.id, "super_admin 強制取消")
    await db.flush()
    return APIResponse(data=asdict(svc.to_view(agent)), message="已取消")


@router.post("/subscriptions/{agent_id}/reactivate", response_model=APIResponse)
async def reactivate_subscription(
    agent_id: str,
    admin: AdminUser = Depends(require_super_admin),
    db: AsyncSession = Depends(get_db),
):
    """重啟已取消(尚未到期)的訂閱。"""
    result = await db.execute(select(AdminUser).where(AdminUser.id == agent_id))
    agent = result.scalar_one_or_none()
    if not agent:
        raise NotFoundError("業務員不存在")
    svc.reactivate(agent)
    await log_action(db, admin, "subscription_reactivate", "agent", agent.id)
    await db.flush()
    return APIResponse(data=asdict(svc.to_view(agent)), message="訂閱已重啟")


# ─────────────────────────────────────────────────────────────
# 外部金流 webhook(預留,未來綠界/Stripe 串接時實作驗證)
# ─────────────────────────────────────────────────────────────


@router.post("/webhook/{provider}", response_model=APIResponse)
async def billing_webhook(
    provider: str,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    # 由全域 default_limits ("120/minute") 提供 rate limit;
    # 加上下方 provider/payload 驗證已足夠防爆 log,故不疊加 @limiter.limit。
    """外部金流回呼。MVP 只 log,不做事。

    Phase 2 會依 provider 解析 payload + 驗簽 → 自動 extend。
    Provider 限制英數字以避免 path injection 攻擊到 log。
    """
    if not provider.replace("_", "").replace("-", "").isalnum() or len(provider) > 30:
        raise BadRequestError("provider 名稱只能是英數字 / -_ 且長度不可超過 30")
    body = await request.body()
    if len(body) > 100 * 1024:   # 100KB 上限
        raise BadRequestError("payload 過大")
    logger.info(f"[billing-webhook] provider={provider} bytes={len(body)}")
    return APIResponse(message=f"webhook {provider} received(尚未實作)")

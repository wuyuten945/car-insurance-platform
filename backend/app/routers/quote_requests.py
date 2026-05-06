"""客戶端詢價工單端點 — 客戶送出 / 列出 / 查看回報"""
from datetime import datetime, timezone
from fastapi import APIRouter, Depends
from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.dependencies import get_db, get_current_user
from app.models.user import User
from app.models.admin_user import AdminUser, AgentCustomer
from app.models.quote_request import QuoteRequest, QuoteResponse
from app.schemas.common import APIResponse
from app.schemas.quote_request import QuoteRequestCreate, QuoteRequestOut, QuoteResponseOut
from app.exceptions import NotFoundError, BadRequestError

router = APIRouter()


def _serialize_request(qr: QuoteRequest) -> dict:
    """轉成前端可用的 dict（含衍生欄位）"""
    return {
        "id": qr.id,
        "user_id": qr.user_id,
        "vehicle_id": qr.vehicle_id,
        "source_policy_id": qr.source_policy_id,
        "use_existing_policy": qr.use_existing_policy,
        "desired_items": qr.desired_items or [],
        "driver_age": qr.driver_age,
        "claims_count_3y": qr.claims_count_3y,
        "surcharge_pct": qr.surcharge_pct,
        "notes": qr.notes,
        "assigned_to_admin_id": qr.assigned_to_admin_id,
        "assigned_admin_name": qr.assigned_admin.display_name if qr.assigned_admin else None,
        "status": qr.status,
        "submitted_at": qr.submitted_at,
        "quoted_at": qr.quoted_at,
        "completed_at": qr.completed_at,
        "customer_name": qr.user.name if qr.user else None,
        "vehicle_plate": qr.vehicle.plate_number if qr.vehicle else None,
        "responses": [QuoteResponseOut.model_validate(r) for r in (qr.responses or [])],
    }


async def _auto_assign_agent(db: AsyncSession, user_id: str) -> str | None:
    """
    依客戶 - 業務員對應表決定指派對象：
    - 若客戶有指派業務員 → 該 agent
    - 沒有 → None（讓 super_admin 共同收件）
    """
    r = await db.execute(
        select(AgentCustomer.agent_id)
        .where(AgentCustomer.customer_id == user_id)
        .order_by(desc(AgentCustomer.assigned_at))
        .limit(1)
    )
    return r.scalar_one_or_none()


@router.post("", response_model=APIResponse)
async def create_quote_request(
    data: QuoteRequestCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """客戶送出詢價工單 → 自動指派給業務員（若有），否則留空待 super_admin 處理"""
    assigned_id = await _auto_assign_agent(db, current_user.id)

    qr = QuoteRequest(
        user_id=current_user.id,
        vehicle_id=data.vehicle_id,
        source_policy_id=data.source_policy_id if data.use_existing_policy else None,
        use_existing_policy=data.use_existing_policy,
        desired_items=[i.model_dump() for i in data.desired_items],
        driver_age=data.driver_age,
        claims_count_3y=data.claims_count_3y,
        surcharge_pct=data.surcharge_pct,
        notes=data.notes,
        assigned_to_admin_id=assigned_id,
        status="pending",
    )
    db.add(qr)
    await db.flush()
    # re-query 帶關聯
    r = await db.execute(
        select(QuoteRequest)
        .options(
            selectinload(QuoteRequest.user),
            selectinload(QuoteRequest.vehicle),
            selectinload(QuoteRequest.assigned_admin),
            selectinload(QuoteRequest.responses),
        )
        .where(QuoteRequest.id == qr.id)
    )
    qr = r.scalar_one()
    return APIResponse(
        data=_serialize_request(qr),
        message="詢價工單已送出，6–12 小時內服務人員會回報您各家保險公司的精確報價",
    )


@router.get("", response_model=APIResponse)
async def list_my_quote_requests(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """列出本人送出的所有詢價工單（最新優先）"""
    r = await db.execute(
        select(QuoteRequest)
        .options(
            selectinload(QuoteRequest.vehicle),
            selectinload(QuoteRequest.assigned_admin),
            selectinload(QuoteRequest.responses),
        )
        .where(QuoteRequest.user_id == current_user.id)
        .order_by(desc(QuoteRequest.submitted_at))
    )
    reqs = list(r.scalars().unique().all())
    # user 已有，不需要 selectinload
    return APIResponse(data=[
        {**_serialize_request(qr), "customer_name": current_user.name}
        for qr in reqs
    ])


@router.get("/{req_id}", response_model=APIResponse)
async def get_quote_request(
    req_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    r = await db.execute(
        select(QuoteRequest)
        .options(
            selectinload(QuoteRequest.user),
            selectinload(QuoteRequest.vehicle),
            selectinload(QuoteRequest.assigned_admin),
            selectinload(QuoteRequest.responses),
        )
        .where(QuoteRequest.id == req_id)
    )
    qr = r.scalar_one_or_none()
    if not qr or qr.user_id != current_user.id:
        raise NotFoundError("詢價工單不存在")
    return APIResponse(data=_serialize_request(qr))


@router.post("/{req_id}/cancel", response_model=APIResponse)
async def cancel_quote_request(
    req_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """客戶取消詢價（只允許 pending / in_progress 階段）"""
    r = await db.execute(select(QuoteRequest).where(QuoteRequest.id == req_id))
    qr = r.scalar_one_or_none()
    if not qr or qr.user_id != current_user.id:
        raise NotFoundError("詢價工單不存在")
    if qr.status in ("completed", "cancelled"):
        raise BadRequestError("此工單已結案，無法取消")
    qr.status = "cancelled"
    qr.completed_at = datetime.now(timezone.utc)
    await db.flush()
    return APIResponse(message="已取消此詢價工單")

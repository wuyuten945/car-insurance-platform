"""
管理後台 API — 管理員管理 / 客戶分配 / 操作日誌 / 資料存取
"""
import logging
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, Request, Query, UploadFile, File
from sqlalchemy import select, and_, func, desc
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from pydantic import BaseModel

from app.dependencies import get_db
from app.models.admin_user import AdminUser, AgentCustomer, AuditLog
from app.models.user import User
from app.models.policy import Policy, PolicyItem
from app.models.vehicle import UserVehicle
from app.models.claim import Claim
from app.core.admin_auth import (
    get_current_admin, require_super_admin, get_accessible_customer_ids,
    hash_password, verify_password, generate_api_key, log_action,
    create_access_token,
)
from app.schemas.common import APIResponse
from app.schemas.user import VehicleCreate, VehicleUpdate, VehicleOut
from app.services.user_service import UserService
from app.core.i18n import t as i18n_t
from app.exceptions import BadRequestError, NotFoundError, ForbiddenError


async def _resolve_vehicle_with_perm(db: AsyncSession, admin: AdminUser, vehicle_id: str) -> UserVehicle:
    """取得車輛 + 權限檢查（agent 只能存取自己的客戶的車輛）"""
    res = await db.execute(select(UserVehicle).where(UserVehicle.id == vehicle_id))
    vehicle = res.scalar_one_or_none()
    if not vehicle:
        raise NotFoundError("車輛不存在")
    accessible = await get_accessible_customer_ids(admin, db)
    if accessible is not None and vehicle.user_id not in accessible:
        raise ForbiddenError("無權限存取此車輛")
    return vehicle


async def _resolve_policy_with_perm(db: AsyncSession, admin: AdminUser, policy_id: str) -> Policy:
    res = await db.execute(select(Policy).where(Policy.id == policy_id))
    policy = res.scalar_one_or_none()
    if not policy:
        raise NotFoundError("保單不存在")
    accessible = await get_accessible_customer_ids(admin, db)
    if accessible is not None and policy.user_id not in accessible:
        raise ForbiddenError("無權限存取此保單")
    return policy


async def _check_customer_perm(db: AsyncSession, admin: AdminUser, customer_id: str):
    res = await db.execute(select(User).where(User.id == customer_id))
    if not res.scalar_one_or_none():
        raise NotFoundError("客戶不存在")
    accessible = await get_accessible_customer_ids(admin, db)
    if accessible is not None and customer_id not in accessible:
        raise ForbiddenError("無權限存取此客戶")

logger = logging.getLogger(__name__)
router = APIRouter()


# ═══════════════════════════════════════════════════
# 登入
# ═══════════════════════════════════════════════════

class AdminLoginRequest(BaseModel):
    username: str
    password: str

@router.post("/login")
async def admin_login(req: AdminLoginRequest, request: Request, db: AsyncSession = Depends(get_db)):
    """管理員帳密登入"""
    result = await db.execute(select(AdminUser).where(AdminUser.username == req.username))
    admin = result.scalar_one_or_none()

    if not admin or not verify_password(req.password, admin.password_hash):
        if admin:
            admin.login_fail_count = str(int(admin.login_fail_count or "0") + 1)
        return APIResponse(success=False, message=i18n_t("admin_invalid_credentials"))

    if not admin.is_active:
        return APIResponse(success=False, message=i18n_t("admin_disabled"))

    # IP 白名單檢查
    client_ip = request.client.host if request.client else ""
    if admin.ip_whitelist:
        allowed = [ip.strip() for ip in admin.ip_whitelist.split(",") if ip.strip()]
        if allowed and client_ip not in allowed:
            await log_action(db, admin, "login_blocked", detail=f"IP {client_ip} not allowed", ip=client_ip)
            return APIResponse(success=False, message=i18n_t("admin_ip_not_allowed", ip=client_ip))

    admin.last_login_at = datetime.now(timezone.utc)
    admin.login_fail_count = "0"

    # 產生管理員專用 JWT（type=admin）
    from jose import jwt
    from app.config import settings
    import time
    token = jwt.encode({
        "sub": admin.id,
        "type": "admin",
        "role": admin.role,
        "exp": int(time.time()) + 28800,  # 8 小時
    }, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)

    await log_action(db, admin, "login", ip=client_ip)

    return APIResponse(data={
        "token": token,
        "admin": {
            "id": admin.id,
            "username": admin.username,
            "display_name": admin.display_name,
            "role": admin.role,
        },
    })


# ═══════════════════════════════════════════════════
# 變更自己的密碼（任何已登入 admin 都可呼叫）
# ═══════════════════════════════════════════════════

class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str


@router.post("/change-password")
async def change_password(
    req: ChangePasswordRequest,
    admin: AdminUser = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """
    變更自己的密碼。安全規則：
      1. 必須已登入（取得有效 token）
      2. 必須輸入舊密碼確認本人（防止 token 被盜後直接改密碼）
      3. 新密碼至少 8 字（簡單複雜度檢查）
      4. 新密碼不可與舊相同
    """
    if not verify_password(req.current_password, admin.password_hash):
        # 不暴露具體哪步錯（避免 brute-force 細分）
        raise BadRequestError(i18n_t("pw_current_wrong"))
    if not req.new_password or len(req.new_password) < 8:
        raise BadRequestError(i18n_t("pw_too_short"))
    if req.new_password == req.current_password:
        raise BadRequestError(i18n_t("pw_same_as_current"))

    admin.password_hash = hash_password(req.new_password)
    # 重置失敗計數
    admin.login_fail_count = "0"
    await log_action(db, admin, "update", "self_password", admin.id, "變更自己密碼")
    return APIResponse(message=i18n_t("pw_change_success"))


# ═══════════════════════════════════════════════════
# 管理員 CRUD（僅 super_admin）
# ═══════════════════════════════════════════════════

class CreateAgentRequest(BaseModel):
    username: str
    password: str
    display_name: str = ""
    email: str = ""
    phone: str = ""
    ip_whitelist: str = ""
    role: str = "agent"  # "agent" 或 "super_admin"（後者僅限 super_admin 呼叫）

@router.post("/agents")
async def create_agent(
    req: CreateAgentRequest,
    admin: AdminUser = Depends(require_super_admin),
    db: AsyncSession = Depends(get_db),
):
    """新增業務員或管理員（super_admin 才能建 super_admin）"""
    existing = await db.execute(select(AdminUser).where(AdminUser.username == req.username))
    if existing.scalar_one_or_none():
        raise BadRequestError(i18n_t("admin_username_exists", username=req.username))

    role = req.role.strip() if req.role else "agent"
    if role not in ("agent", "super_admin"):
        raise BadRequestError(i18n_t("pw_invalid_role", role=role))

    agent = AdminUser(
        username=req.username,
        password_hash=hash_password(req.password),
        display_name=req.display_name or req.username,
        email=req.email, phone=req.phone,
        role=role,
        api_key=generate_api_key(),
        ip_whitelist=req.ip_whitelist,
    )
    db.add(agent)
    await db.flush()
    await log_action(db, admin, "create", "agent", agent.id, f"新增業務員 {req.username}")

    return APIResponse(data={
        "id": agent.id, "username": agent.username,
        "display_name": agent.display_name, "api_key": agent.api_key,
    }, message=f"業務員 {req.username} 已建立")


@router.get("/agents")
async def list_agents(
    admin: AdminUser = Depends(require_super_admin),
    db: AsyncSession = Depends(get_db),
):
    """列出所有業務員"""
    result = await db.execute(
        select(AdminUser).where(AdminUser.role == "agent").order_by(AdminUser.created_at.desc())
    )
    agents = []
    for a in result.scalars().all():
        # 統計客戶數
        cnt = await db.execute(
            select(func.count()).where(AgentCustomer.agent_id == a.id)
        )
        agents.append({
            "id": a.id, "username": a.username, "display_name": a.display_name,
            "email": a.email, "phone": a.phone,
            "is_active": a.is_active, "role": a.role,
            "api_key": a.api_key[:8] + "..." if a.api_key else "",
            "ip_whitelist": a.ip_whitelist or "",
            "customer_count": cnt.scalar() or 0,
            "last_login": a.last_login_at.isoformat() if a.last_login_at else None,
            "created_at": a.created_at.isoformat(),
        })
    return APIResponse(data=agents)


class UpdateAgentRequest(BaseModel):
    display_name: str | None = None
    email: str | None = None
    phone: str | None = None
    password: str | None = None
    is_active: bool | None = None
    ip_whitelist: str | None = None
    role: str | None = None  # 'agent' 或 'super_admin'

@router.patch("/agents/{agent_id}")
async def update_agent(
    agent_id: str, req: UpdateAgentRequest,
    admin: AdminUser = Depends(require_super_admin),
    db: AsyncSession = Depends(get_db),
):
    """更新/停用業務員"""
    result = await db.execute(select(AdminUser).where(AdminUser.id == agent_id))
    agent = result.scalar_one_or_none()
    if not agent:
        raise NotFoundError(i18n_t("admin_not_found"))

    changes = []
    if req.display_name is not None:
        agent.display_name = req.display_name; changes.append("名稱")
    if req.email is not None:
        agent.email = req.email; changes.append("Email")
    if req.phone is not None:
        agent.phone = req.phone; changes.append("電話")
    if req.password is not None:
        agent.password_hash = hash_password(req.password); changes.append("密碼")
    if req.is_active is not None:
        agent.is_active = req.is_active; changes.append("啟用" if req.is_active else "停用")
    if req.ip_whitelist is not None:
        agent.ip_whitelist = req.ip_whitelist; changes.append("IP白名單")
    if req.role is not None:
        if req.role not in ("agent", "super_admin"):
            raise BadRequestError(i18n_t("pw_invalid_role", role=req.role))
        agent.role = req.role; changes.append(f"角色={req.role}")

    await log_action(db, admin, "update", "agent", agent_id, f"更新: {','.join(changes)}")
    return APIResponse(message=f"業務員已更新（{','.join(changes)}）")


@router.post("/agents/{agent_id}/reset-api-key")
async def reset_api_key(
    agent_id: str,
    admin: AdminUser = Depends(require_super_admin),
    db: AsyncSession = Depends(get_db),
):
    """重置業務員 API Key"""
    result = await db.execute(select(AdminUser).where(AdminUser.id == agent_id))
    agent = result.scalar_one_or_none()
    if not agent:
        raise NotFoundError("業務員不存在")
    agent.api_key = generate_api_key()
    await log_action(db, admin, "reset_api_key", "agent", agent_id)
    return APIResponse(data={"api_key": agent.api_key}, message="API Key 已重置")


# ═══════════════════════════════════════════════════
# 客戶分配
# ═══════════════════════════════════════════════════

class AssignCustomerRequest(BaseModel):
    agent_id: str
    customer_id: str

@router.post("/assign-customer")
async def assign_customer(
    req: AssignCustomerRequest,
    admin: AdminUser = Depends(require_super_admin),
    db: AsyncSession = Depends(get_db),
):
    """分配客戶給業務員"""
    existing = await db.execute(select(AgentCustomer).where(
        and_(AgentCustomer.agent_id == req.agent_id, AgentCustomer.customer_id == req.customer_id)
    ))
    if existing.scalar_one_or_none():
        raise BadRequestError("此客戶已分配給此業務員")

    db.add(AgentCustomer(
        agent_id=req.agent_id, customer_id=req.customer_id, assigned_by=admin.id,
    ))
    await log_action(db, admin, "assign", "customer", req.customer_id,
                     f"分配給業務員 {req.agent_id}")
    return APIResponse(message="客戶已分配")


@router.delete("/assign-customer")
async def unassign_customer(
    agent_id: str = Query(...), customer_id: str = Query(...),
    admin: AdminUser = Depends(require_super_admin),
    db: AsyncSession = Depends(get_db),
):
    """取消客戶分配"""
    result = await db.execute(select(AgentCustomer).where(
        and_(AgentCustomer.agent_id == agent_id, AgentCustomer.customer_id == customer_id)
    ))
    ac = result.scalar_one_or_none()
    if ac:
        await db.delete(ac)
        await log_action(db, admin, "unassign", "customer", customer_id)
    return APIResponse(message="已取消分配")


@router.get("/search")
async def quick_search(
    q: str = Query(..., min_length=1, description="關鍵字（姓名/電話/Email/車牌/保單號/理賠號）"),
    limit: int = Query(20, ge=1, le=100),
    admin: AdminUser = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """
    全域快速搜尋（客戶 / 車輛 / 保單 / 理賠四類），權限會自動套用：
      super_admin → 全部資料
      agent → 只搜自己分配的客戶 + 該客戶名下的車輛/保單/理賠
    """
    keyword = q.strip()
    if not keyword:
        return APIResponse(data={"customers": [], "vehicles": [], "policies": [], "claims": []})

    accessible = await get_accessible_customer_ids(admin, db)
    like_kw = f"%{keyword}%"

    # 1. 客戶（姓名 / 電話 / Email）
    cust_q = select(User).where(
        (User.name.ilike(like_kw)) | (User.phone.ilike(like_kw)) | (User.email.ilike(like_kw))
    )
    if accessible is not None:
        cust_q = cust_q.where(User.id.in_(accessible))
    cust_rows = (await db.execute(cust_q.limit(limit))).scalars().all()

    # 2. 車輛（車牌 / 廠牌 / 型號）
    veh_q = select(UserVehicle).options(selectinload(UserVehicle.user)).where(
        (UserVehicle.plate_number.ilike(like_kw)) |
        (UserVehicle.brand.ilike(like_kw)) |
        (UserVehicle.model.ilike(like_kw))
    )
    if accessible is not None:
        veh_q = veh_q.where(UserVehicle.user_id.in_(accessible))
    veh_rows = (await db.execute(veh_q.limit(limit))).scalars().all()

    # 3. 保單（保單號 / 保險公司）
    pol_q = select(Policy).options(selectinload(Policy.user)).where(
        (Policy.policy_number.ilike(like_kw)) | (Policy.insurer_name.ilike(like_kw))
    )
    if accessible is not None:
        pol_q = pol_q.where(Policy.user_id.in_(accessible))
    pol_rows = (await db.execute(pol_q.limit(limit))).scalars().all()

    # 4. 理賠（案件號）
    clm_q = select(Claim).options(selectinload(Claim.user)).where(
        Claim.claim_number.ilike(like_kw)
    )
    if accessible is not None:
        clm_q = clm_q.where(Claim.user_id.in_(accessible))
    clm_rows = (await db.execute(clm_q.limit(limit))).scalars().all()

    await log_action(db, admin, "search", "global", detail=f"q={keyword}")

    return APIResponse(data={
        "keyword": keyword,
        "customers": [
            {"id": c.id, "name": c.name, "phone": c.phone, "email": c.email}
            for c in cust_rows
        ],
        "vehicles": [
            {
                "id": v.id, "plate_number": v.plate_number,
                "brand": v.brand, "model": v.model, "year": v.year,
                "user_id": v.user_id,
                "user_name": v.user.name if v.user else None,
            }
            for v in veh_rows
        ],
        "policies": [
            {
                "id": p.id, "policy_number": p.policy_number,
                "insurer_name": p.insurer_name, "status": p.status,
                "start_date": str(p.start_date) if p.start_date else None,
                "end_date": str(p.end_date) if p.end_date else None,
                "user_id": p.user_id,
                "user_name": p.user.name if p.user else None,
            }
            for p in pol_rows
        ],
        "claims": [
            {
                "id": cl.id, "claim_number": cl.claim_number,
                "status": cl.status, "claim_type": cl.claim_type,
                "submitted_at": cl.submitted_at.isoformat() if cl.submitted_at else None,
                "user_id": cl.user_id,
                "user_name": cl.user.name if cl.user else None,
            }
            for cl in clm_rows
        ],
    })


@router.get("/customers")
async def list_customers(
    admin: AdminUser = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """列出可存取的客戶（agent 只看自己的）"""
    accessible = await get_accessible_customer_ids(admin, db)
    query = select(User)
    if accessible is not None:
        query = query.where(User.id.in_(accessible))
    query = query.order_by(User.created_at.desc())
    result = await db.execute(query)
    customers = []
    for u in result.scalars().all():
        customers.append({
            "id": u.id, "name": u.name, "phone": u.phone, "email": u.email,
            "created_at": u.created_at.isoformat(),
        })
    await log_action(db, admin, "view", "customer_list", detail=f"{len(customers)} 筆")
    return APIResponse(data=customers)


# ═══════════════════════════════════════════════════
# 操作日誌
# ═══════════════════════════════════════════════════

@router.get("/audit-logs")
async def list_audit_logs(
    agent_id: str = Query(None),
    action: str = Query(None),
    page: int = Query(1, ge=1),
    per_page: int = Query(50, ge=1, le=200),
    admin: AdminUser = Depends(require_super_admin),
    db: AsyncSession = Depends(get_db),
):
    """查看操作日誌（僅 super_admin）"""
    query = select(AuditLog).options(selectinload(AuditLog.admin_user))
    if agent_id:
        query = query.where(AuditLog.admin_user_id == agent_id)
    if action:
        query = query.where(AuditLog.action == action)
    query = query.order_by(desc(AuditLog.timestamp))
    query = query.offset((page - 1) * per_page).limit(per_page)

    result = await db.execute(query)
    logs = []
    for log in result.scalars().all():
        logs.append({
            "id": log.id,
            "admin": log.admin_user.display_name if log.admin_user else log.admin_user_id,
            "action": log.action,
            "target_type": log.target_type,
            "target_id": log.target_id,
            "detail": log.detail,
            "ip": log.ip_address,
            "timestamp": log.timestamp.isoformat() if log.timestamp else "",
        })
    return APIResponse(data=logs)


# ═══════════════════════════════════════════════════
# 資料存取（受權限控制）
# ═══════════════════════════════════════════════════

# ═══════════════════════════════════════════════════
# 全部資料（admin 看跨客戶）
# ═══════════════════════════════════════════════════

@router.get("/all/vehicles")
async def get_all_vehicles(
    admin: AdminUser = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """列出可存取的全部車輛（含客戶資訊與行照）。

    為相容既有 admin.py UI，車輛欄位用「長 key」（plate_number 等）。
    """
    accessible = await get_accessible_customer_ids(admin, db)
    query = select(UserVehicle).options(selectinload(UserVehicle.user))
    if accessible is not None:
        query = query.where(UserVehicle.user_id.in_(accessible))
    query = query.order_by(UserVehicle.created_at.desc())
    result = await db.execute(query)
    rows = []
    for v in result.scalars().all():
        rows.append({
            "id": v.id,
            "user_id": v.user_id,
            "customer_name": v.user.name if v.user else None,
            "customer_phone": v.user.phone if v.user else None,
            "customer_email": v.user.email if v.user else None,
            "plate_number": v.plate_number,
            "brand": v.brand,
            "model": v.model,
            "year": v.year,
            "manufacture_month": v.manufacture_month,
            "color": v.color,
            "vin": v.vin,
            "engine_cc": v.engine_cc,
            "fuel_type": v.fuel_type,
            "vehicle_type": v.vehicle_type,
            "is_primary": v.is_primary,
            "registration_image_url": v.registration_image_url,
            "registration_date": str(v.registration_date) if v.registration_date else None,
            "reissue_date": str(v.reissue_date) if v.reissue_date else None,
            "registration_expiry": str(v.registration_expiry) if v.registration_expiry else None,
            "last_inspection_date": str(v.last_inspection_date) if v.last_inspection_date else None,
        })
    await log_action(db, admin, "view", "all_vehicles", detail=f"{len(rows)} 筆")
    return APIResponse(data=rows)


@router.get("/all/policies")
async def get_all_policies(
    admin: AdminUser = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """列出可存取的全部保單（含客戶資訊、車輛、items）"""
    accessible = await get_accessible_customer_ids(admin, db)
    query = (
        select(Policy)
        .options(selectinload(Policy.items), selectinload(Policy.user), selectinload(Policy.vehicle))
    )
    if accessible is not None:
        query = query.where(Policy.user_id.in_(accessible))
    query = query.order_by(Policy.start_date.desc())
    result = await db.execute(query)
    rows = []
    for p in result.scalars().all():
        items = [{
            "item_name": it.item_name,
            "premium": float(it.premium) if it.premium else 0,
            "coverage_limit": float(it.coverage_limit) if it.coverage_limit else None,
            "deductible": float(it.deductible) if it.deductible else None,
            "is_active": it.is_active,
            "description": it.description,
        } for it in p.items]
        rows.append({
            "id": p.id,
            "user_id": p.user_id,
            "customer_name": p.user.name if p.user else None,
            "customer_phone": p.user.phone if p.user else None,
            "customer_email": p.user.email if p.user else None,
            "vehicle_id": p.vehicle_id,
            "vehicle_plate": p.vehicle.plate_number if p.vehicle else None,
            "insurer_name": p.insurer_name,
            "policy_number": p.policy_number,
            "status": p.status,
            "start_date": str(p.start_date),
            "end_date": str(p.end_date),
            "start_time": p.start_time.strftime("%H:%M") if p.start_time else None,
            "end_time": p.end_time.strftime("%H:%M") if p.end_time else None,
            "compulsory_insurer_name": p.compulsory_insurer_name,
            "compulsory_policy_number": p.compulsory_policy_number,
            "compulsory_premium": float(p.compulsory_premium) if p.compulsory_premium else None,
            "compulsory_start_date": str(p.compulsory_start_date) if p.compulsory_start_date else None,
            "compulsory_end_date": str(p.compulsory_end_date) if p.compulsory_end_date else None,
            "compulsory_start_time": p.compulsory_start_time.strftime("%H:%M") if p.compulsory_start_time else None,
            "compulsory_end_time": p.compulsory_end_time.strftime("%H:%M") if p.compulsory_end_time else None,
            "total_premium": float(p.total_premium) if p.total_premium else 0,
            "items": items,
        })
    await log_action(db, admin, "view", "all_policies", detail=f"{len(rows)} 筆")
    return APIResponse(data=rows)


@router.get("/all/overview")
async def get_overview(
    admin: AdminUser = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """總覽統計"""
    from datetime import date
    today = date.today()

    accessible = await get_accessible_customer_ids(admin, db)

    # 客戶數
    user_q = select(func.count()).select_from(User)
    if accessible is not None:
        user_q = user_q.where(User.id.in_(accessible))
    customer_count = (await db.execute(user_q)).scalar() or 0

    # 車輛數
    veh_q = select(func.count()).select_from(UserVehicle)
    if accessible is not None:
        veh_q = veh_q.where(UserVehicle.user_id.in_(accessible))
    vehicle_count = (await db.execute(veh_q)).scalar() or 0

    # 保單統計
    pol_q = select(Policy)
    if accessible is not None:
        pol_q = pol_q.where(Policy.user_id.in_(accessible))
    policies = (await db.execute(pol_q)).scalars().all()

    active = sum(1 for p in policies if p.status == "active")
    expiring = sum(1 for p in policies if p.status == "expiring")
    expired = sum(1 for p in policies if p.status == "expired")
    total_premium = sum(float(p.total_premium or 0) for p in policies)

    # 30 天內到期
    upcoming = []
    for p in policies:
        if p.status in ("active", "expiring") and p.end_date:
            days = (p.end_date - today).days
            if 0 <= days <= 30:
                upcoming.append({
                    "policy_number": p.policy_number,
                    "insurer": p.insurer_name,
                    "end_date": str(p.end_date),
                    "days_left": days,
                })
    upcoming.sort(key=lambda x: x["days_left"])

    return APIResponse(data={
        "customer_count": customer_count,
        "vehicle_count": vehicle_count,
        "policy_count": len(policies),
        "policy_active": active,
        "policy_expiring": expiring,
        "policy_expired": expired,
        "total_premium": round(total_premium, 2),
        "upcoming_30d": upcoming[:20],
    })


@router.get("/customer/{customer_id}/policies")
async def get_customer_policies(
    customer_id: str,
    admin: AdminUser = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """查看客戶保單（含 items 明細）"""
    accessible = await get_accessible_customer_ids(admin, db)
    if accessible is not None and customer_id not in accessible:
        raise ForbiddenError("無權限存取此客戶")
    result = await db.execute(
        select(Policy).options(selectinload(Policy.items), selectinload(Policy.vehicle))
        .where(Policy.user_id == customer_id)
        .order_by(Policy.start_date.desc())
    )
    policies = []
    for p in result.scalars().all():
        items = [{
            "id": it.id,
            "item_name": it.item_name,
            "premium": float(it.premium) if it.premium else 0,
            "coverage_limit": float(it.coverage_limit) if it.coverage_limit else None,
            "deductible": float(it.deductible) if it.deductible else None,
            "is_active": it.is_active,
            "description": it.description,
        } for it in p.items]
        policies.append({
            "id": p.id, "insurer": p.insurer_name, "number": p.policy_number,
            "status": p.status, "start": str(p.start_date), "end": str(p.end_date),
            "premium": float(p.total_premium) if p.total_premium else 0,
            "vehicle_id": p.vehicle_id,
            "vehicle_plate": p.vehicle.plate_number if p.vehicle else None,
            "items": items,
        })
    await log_action(db, admin, "view", "policies", customer_id)
    return APIResponse(data=policies)


@router.get("/customer/{customer_id}/vehicles")
async def get_customer_vehicles(
    customer_id: str,
    admin: AdminUser = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """查看客戶車輛（含完整欄位 + 行照圖片）"""
    accessible = await get_accessible_customer_ids(admin, db)
    if accessible is not None and customer_id not in accessible:
        raise ForbiddenError("無權限存取此客戶")
    result = await db.execute(select(UserVehicle).where(UserVehicle.user_id == customer_id))
    vehicles = [{
        "id": v.id,
        "plate": v.plate_number,
        "brand": v.brand,
        "model": v.model,
        "year": v.year,
        "manufacture_month": v.manufacture_month,
        "color": v.color,
        "vin": v.vin,
        "engine_cc": v.engine_cc,
        "fuel_type": v.fuel_type,
        "vehicle_type": v.vehicle_type,
        "is_primary": v.is_primary,
        "registration_image_url": v.registration_image_url,
        "registration_date": str(v.registration_date) if v.registration_date else None,
        "reissue_date": str(v.reissue_date) if v.reissue_date else None,
        "registration_expiry": str(v.registration_expiry) if v.registration_expiry else None,
        "last_inspection_date": str(v.last_inspection_date) if v.last_inspection_date else None,
    } for v in result.scalars().all()]
    await log_action(db, admin, "view", "vehicles", customer_id)
    return APIResponse(data=vehicles)


# ═══════════════════════════════════════════════════
# 客戶資料編輯（補 email、改姓名等）
# ═══════════════════════════════════════════════════

class CustomerUpdateRequest(BaseModel):
    name: str | None = None
    email: str | None = None
    phone: str | None = None


@router.patch("/customer/{customer_id}")
async def update_customer(
    customer_id: str,
    req: CustomerUpdateRequest,
    admin: AdminUser = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """更新客戶基本資料（admin/agent 補 email 給 phone-only 用戶用）"""
    accessible = await get_accessible_customer_ids(admin, db)
    if accessible is not None and customer_id not in accessible:
        raise ForbiddenError("無權限存取此客戶")

    result = await db.execute(select(User).where(User.id == customer_id))
    user = result.scalar_one_or_none()
    if not user:
        raise NotFoundError("客戶不存在")

    changes = []
    if req.name is not None and req.name != user.name:
        user.name = req.name.strip() or None
        changes.append(f"name={user.name}")
    if req.email is not None:
        new_email = (req.email or "").strip().lower() or None
        if new_email and new_email != user.email:
            # 檢查 email 不重複（避免撞 unique）
            dup = await db.execute(select(User).where(User.email == new_email, User.id != customer_id))
            if dup.scalar_one_or_none():
                raise BadRequestError(f"Email 已被其他客戶使用：{new_email}")
            user.email = new_email
            changes.append(f"email={new_email}")
        elif new_email is None and user.email:
            user.email = None
            changes.append("email=NULL")
    if req.phone is not None:
        new_phone = (req.phone or "").strip() or None
        if new_phone != user.phone:
            if new_phone:
                dup = await db.execute(select(User).where(User.phone == new_phone, User.id != customer_id))
                if dup.scalar_one_or_none():
                    raise BadRequestError(f"電話已被其他客戶使用：{new_phone}")
            user.phone = new_phone
            changes.append(f"phone={new_phone}")

    if not changes:
        return APIResponse(data={"updated": False}, message="無變更")

    await db.commit()
    await log_action(db, admin, "update", "customer", customer_id, detail="; ".join(changes))
    return APIResponse(data={
        "id": user.id, "name": user.name, "phone": user.phone, "email": user.email,
        "changed": changes,
    }, message="已更新")


# ═══════════════════════════════════════════════════
# 重複客戶偵測 + 合併（OAuth 自助登入後可能與既有客戶分離）
# ═══════════════════════════════════════════════════

@router.get("/customers/duplicates")
async def find_duplicate_customers(
    admin: AdminUser = Depends(require_super_admin),
    db: AsyncSession = Depends(get_db),
):
    """找出可能重複的客戶（同 id_number_hash、或同名+生日）。僅 super_admin。"""
    # 同 id_number_hash 的不同 user
    result = await db.execute(
        select(User.id_number_hash, func.count(User.id).label("cnt"))
        .where(User.id_number_hash.isnot(None), User.id_number_hash != "")
        .group_by(User.id_number_hash)
        .having(func.count(User.id) > 1)
    )
    same_idn = []
    for row in result.all():
        users_res = await db.execute(select(User).where(User.id_number_hash == row[0]))
        users = users_res.scalars().all()
        same_idn.append({
            "match_type": "id_number",
            "users": [{"id": u.id, "name": u.name, "phone": u.phone, "email": u.email,
                       "created_at": u.created_at.isoformat() if u.created_at else None}
                      for u in users],
        })

    # 同名+同生日（簡化重複偵測，可調整）
    result = await db.execute(
        select(User.name, User.birth_date, func.count(User.id).label("cnt"))
        .where(User.name.isnot(None), User.birth_date.isnot(None))
        .group_by(User.name, User.birth_date)
        .having(func.count(User.id) > 1)
    )
    same_namebd = []
    for row in result.all():
        users_res = await db.execute(
            select(User).where(User.name == row[0], User.birth_date == row[1])
        )
        users = users_res.scalars().all()
        same_namebd.append({
            "match_type": "name_birthdate",
            "users": [{"id": u.id, "name": u.name, "phone": u.phone, "email": u.email,
                       "created_at": u.created_at.isoformat() if u.created_at else None}
                      for u in users],
        })

    return APIResponse(data={
        "by_id_number": same_idn,
        "by_name_birthdate": same_namebd,
        "total_groups": len(same_idn) + len(same_namebd),
    })


class MergeUsersRequest(BaseModel):
    primary_user_id: str   # 保留的主帳號（合併到這個）
    secondary_user_id: str  # 要合併進去並刪除的帳號


@router.post("/customers/merge")
async def merge_customers(
    req: MergeUsersRequest,
    admin: AdminUser = Depends(require_super_admin),
    db: AsyncSession = Depends(get_db),
):
    """把 secondary 用戶的所有資料合併到 primary，並刪除 secondary。僅 super_admin。

    合併內容：
    - 轉移 vehicles, policies, accidents, claims, notifications 的 user_id
    - 補 primary 缺的 email/phone/name/id_number_hash 等基本欄位
    - secondary 刪除
    """
    if req.primary_user_id == req.secondary_user_id:
        raise BadRequestError("不能合併同一個帳號")

    p_res = await db.execute(select(User).where(User.id == req.primary_user_id))
    primary = p_res.scalar_one_or_none()
    s_res = await db.execute(select(User).where(User.id == req.secondary_user_id))
    secondary = s_res.scalar_one_or_none()
    if not primary or not secondary:
        raise NotFoundError("主帳號或次帳號不存在")

    transferred = {}
    # 動態 import 避免循環依賴
    from app.models.accident import Accident
    from app.models.claim import Claim
    from app.models.notification import Notification

    for model_cls, label in [
        (UserVehicle, "vehicles"),
        (Policy, "policies"),
        (Accident, "accidents"),
        (Claim, "claims"),
        (Notification, "notifications"),
    ]:
        res = await db.execute(select(model_cls).where(model_cls.user_id == secondary.id))
        items = res.scalars().all()
        for it in items:
            it.user_id = primary.id
        transferred[label] = len(items)

    # 補欄位（primary 沒有但 secondary 有的）
    for field in ["name", "phone", "email", "id_number_hash", "birth_date", "address",
                  "registered_address", "emergency_contact_name", "emergency_contact_phone",
                  "emergency_contact_relation", "license_number", "license_expiry"]:
        p_val = getattr(primary, field, None)
        s_val = getattr(secondary, field, None)
        if not p_val and s_val:
            # 若是 phone/email 被合併時要避免衝突（理論上不會，因為 primary 沒這欄）
            setattr(primary, field, s_val)
            transferred[f"filled_{field}"] = True

    # 為了避免 unique 衝突，先把 secondary 的 unique 欄位清空再 delete
    secondary.phone = None
    secondary.email = None
    await db.flush()
    await db.delete(secondary)
    await db.commit()

    await log_action(
        db, admin, "merge", "customer", primary.id,
        detail=f"merged from={secondary.id} → {primary.id}; transferred={transferred}",
    )
    return APIResponse(data={
        "primary": {"id": primary.id, "name": primary.name, "email": primary.email, "phone": primary.phone},
        "transferred": transferred,
    }, message="合併成功")


# ═══════════════════════════════════════════════════
# 車輛操作（admin 代客戶執行）
# ═══════════════════════════════════════════════════

@router.post("/customer/{customer_id}/vehicles")
async def admin_create_vehicle(
    customer_id: str,
    data: VehicleCreate,
    admin: AdminUser = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """為指定客戶新增車輛"""
    await _check_customer_perm(db, admin, customer_id)
    svc = UserService(db)
    vehicle = await svc.create_vehicle(customer_id, data)
    await db.commit()
    await log_action(db, admin, "create", "vehicle", vehicle.id, detail=f"plate={vehicle.plate_number} for customer={customer_id}")
    return APIResponse(data=VehicleOut.model_validate(vehicle), message="車輛已新增")


@router.patch("/vehicles/{vehicle_id}")
async def admin_patch_vehicle(
    vehicle_id: str,
    data: VehicleUpdate,
    admin: AdminUser = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """編輯車輛資料"""
    vehicle = await _resolve_vehicle_with_perm(db, admin, vehicle_id)
    svc = UserService(db)
    updated = await svc.patch_vehicle(vehicle.user_id, vehicle_id, data)
    await db.commit()
    await log_action(db, admin, "update", "vehicle", vehicle_id, detail=str(data.model_dump(exclude_unset=True))[:200])
    return APIResponse(data=VehicleOut.model_validate(updated), message="車輛已更新")


@router.delete("/vehicles/{vehicle_id}")
async def admin_delete_vehicle(
    vehicle_id: str,
    admin: AdminUser = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """刪除車輛"""
    vehicle = await _resolve_vehicle_with_perm(db, admin, vehicle_id)
    plate = vehicle.plate_number
    await db.delete(vehicle)
    await db.commit()
    await log_action(db, admin, "delete", "vehicle", vehicle_id, detail=f"plate={plate}")
    return APIResponse(message="車輛已刪除")


# ═══════════════════════════════════════════════════
# 車輛「轉移到不同客戶」+ 新建客戶（給編輯表單用）
# ═══════════════════════════════════════════════════

class TransferVehicleRequest(BaseModel):
    customer_id: str


@router.post("/vehicles/{vehicle_id}/transfer")
async def admin_transfer_vehicle(
    vehicle_id: str,
    req: TransferVehicleRequest,
    admin: AdminUser = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """把車輛轉移到另一個客戶（含該車輛的所有保單也跟著轉）"""
    vehicle = await _resolve_vehicle_with_perm(db, admin, vehicle_id)
    if not req.customer_id:
        raise BadRequestError("customer_id 必填")
    await _check_customer_perm(db, admin, req.customer_id)
    old_uid = vehicle.user_id
    if old_uid == req.customer_id:
        return APIResponse(message="車輛已屬於此客戶，無需轉移")
    vehicle.user_id = req.customer_id
    # 同步轉移該車的所有保單
    res = await db.execute(select(Policy).where(Policy.vehicle_id == vehicle_id))
    transferred_policies = 0
    for p in res.scalars().all():
        p.user_id = req.customer_id
        transferred_policies += 1
    await db.commit()
    await log_action(db, admin, "transfer", "vehicle", vehicle_id,
                     detail=f"plate={vehicle.plate_number} {old_uid}→{req.customer_id} (含 {transferred_policies} 張保單)")
    return APIResponse(message=f"車輛已轉移（含 {transferred_policies} 張保單）")


@router.post("/policies/{policy_id}/transfer")
async def admin_transfer_policy(
    policy_id: str,
    req: TransferVehicleRequest,
    admin: AdminUser = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """把保單轉移到另一個客戶（要保人變更）— 不動車輛歸屬"""
    policy = await _resolve_policy_with_perm(db, admin, policy_id)
    if not req.customer_id:
        raise BadRequestError("customer_id 必填")
    await _check_customer_perm(db, admin, req.customer_id)
    old_uid = policy.user_id
    if old_uid == req.customer_id:
        return APIResponse(message="保單已屬於此客戶，無需轉移")
    policy.user_id = req.customer_id
    await db.commit()
    await log_action(db, admin, "transfer", "policy", policy_id,
                     detail=f"policy_number={policy.policy_number} {old_uid}→{req.customer_id}")
    return APIResponse(message="保單要保人已變更")


class CreateCustomerRequest(BaseModel):
    name: str
    phone: str | None = None
    email: str | None = None


@router.post("/customers")
async def admin_create_customer(
    req: CreateCustomerRequest,
    admin: AdminUser = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """admin 直接新建客戶（不需 OTP，給「車輛指定到新客戶」流程用）"""
    name = (req.name or "").strip()
    if not name:
        raise BadRequestError("姓名不能為空")
    phone = (req.phone or "").strip() or None
    email = (req.email or "").strip() or None
    # 重複檢查
    if phone:
        dup = await db.execute(select(User).where(User.phone == phone))
        if dup.scalar_one_or_none():
            raise BadRequestError(f"電話已被其他客戶使用：{phone}")
    if email:
        dup = await db.execute(select(User).where(User.email == email))
        if dup.scalar_one_or_none():
            raise BadRequestError(f"Email 已被其他客戶使用：{email}")
    user = User(name=name, phone=phone, email=email)
    db.add(user)
    await db.commit()
    await log_action(db, admin, "create", "customer", user.id, detail=f"name={name}")
    return APIResponse(data={
        "id": user.id, "name": user.name,
        "phone": user.phone, "email": user.email,
    }, message="客戶已建立")


@router.post("/vehicles/{vehicle_id}/registration")
async def admin_upload_registration(
    vehicle_id: str,
    file: UploadFile = File(..., description="行照圖片或 PDF"),
    admin: AdminUser = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """上傳行照（admin 代客戶）"""
    vehicle = await _resolve_vehicle_with_perm(db, admin, vehicle_id)
    svc = UserService(db)
    updated = await svc.upload_registration(vehicle.user_id, vehicle_id, file)
    await db.commit()
    await log_action(db, admin, "upload", "registration", vehicle_id)
    return APIResponse(
        data={
            "vehicle": VehicleOut.model_validate(updated),
            "ocr_result": None,
            "ocr_available": False,
        },
        message="行照已上傳，可點擊 AI 辨識自動填入車輛資料",
    )


@router.post("/vehicles/{vehicle_id}/ocr")
async def admin_ocr_registration(
    vehicle_id: str,
    admin: AdminUser = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """對車輛行照執行 OCR（admin 代客戶）"""
    from pathlib import Path
    from datetime import date as _date
    from app.core.ocr_registration import analyze_registration
    from app.config import settings as _s

    vehicle = await _resolve_vehicle_with_perm(db, admin, vehicle_id)
    if not vehicle.registration_image_url:
        raise BadRequestError("請先上傳行照圖片")

    image_path = str(Path(_s.UPLOAD_DIR) / "registrations" / Path(vehicle.registration_image_url).name)
    if not Path(image_path).exists():
        image_path = str((Path(_s.UPLOAD_DIR) / vehicle.registration_image_url.lstrip("/uploads/")).resolve())

    ocr_result = await analyze_registration(image_path)

    if ocr_result and "error" not in ocr_result:
        for field in ("plate_number", "brand", "model", "color", "vin", "vehicle_type", "fuel_type"):
            val = ocr_result.get(field)
            if val:
                setattr(vehicle, field, str(val))
        if ocr_result.get("year"):
            try: vehicle.year = int(ocr_result["year"])
            except (ValueError, TypeError): pass
        if ocr_result.get("engine_cc"):
            try: vehicle.engine_cc = int(ocr_result["engine_cc"])
            except (ValueError, TypeError): pass
        for date_field in ("registration_date", "registration_expiry"):
            val = ocr_result.get(date_field)
            if val:
                try: setattr(vehicle, date_field, _date.fromisoformat(val))
                except (ValueError, TypeError): pass
        await db.commit()

    has_ocr = ocr_result and "error" not in ocr_result
    await log_action(db, admin, "ocr", "registration", vehicle_id)
    return APIResponse(
        data={
            "vehicle": VehicleOut.model_validate(vehicle),
            "ocr_result": ocr_result if has_ocr else None,
            "ocr_available": has_ocr,
        },
        message="AI 辨識完成" if has_ocr else f"辨識失敗: {(ocr_result or {}).get('error','')}",
    )



# ═══════════════════════════════════════════════════
# 保單操作（admin 代客戶執行）
# ═══════════════════════════════════════════════════

@router.post("/customer/{customer_id}/policies")
async def admin_create_policy(
    customer_id: str,
    data: dict,
    admin: AdminUser = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """為指定客戶建立保單"""
    from app.schemas.policy import PolicyCreate, PolicyDetailOut, PolicyItemOut
    from app.services.policy_service import PolicyService
    from datetime import date

    await _check_customer_perm(db, admin, customer_id)
    policy_data = PolicyCreate.model_validate(data)
    svc = PolicyService(db)
    policy = await svc.create_policy(customer_id, policy_data)
    await db.commit()
    today = date.today()
    days_remaining = (policy.end_date - today).days if policy.end_date >= today else 0
    await log_action(db, admin, "create", "policy", policy.id, detail=f"insurer={policy.insurer_name}")
    return APIResponse(
        data=PolicyDetailOut(
            id=policy.id, insurer_name=policy.insurer_name, policy_number=policy.policy_number,
            status=policy.status, start_date=policy.start_date, end_date=policy.end_date,
            total_premium=policy.total_premium, days_remaining=days_remaining,
            document_url=policy.document_url, created_at=policy.created_at,
            items=[PolicyItemOut.model_validate(i) for i in policy.items],
        ),
        message="保單已建立",
    )


@router.put("/policies/{policy_id}")
async def admin_update_policy(
    policy_id: str,
    data: dict,
    admin: AdminUser = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """更新保單"""
    from app.schemas.policy import PolicyUpdate, PolicyDetailOut, PolicyItemOut
    from app.services.policy_service import PolicyService
    from datetime import date

    policy = await _resolve_policy_with_perm(db, admin, policy_id)
    update_data = PolicyUpdate.model_validate(data)
    svc = PolicyService(db)
    updated = await svc.update_policy(policy.user_id, policy_id, update_data)
    await db.commit()
    today = date.today()
    days_remaining = (updated.end_date - today).days if updated.end_date >= today else 0
    await log_action(db, admin, "update", "policy", policy_id, detail=str(data)[:200])
    return APIResponse(
        data=PolicyDetailOut(
            id=updated.id, insurer_name=updated.insurer_name, policy_number=updated.policy_number,
            status=updated.status, start_date=updated.start_date, end_date=updated.end_date,
            total_premium=updated.total_premium, days_remaining=days_remaining,
            document_url=updated.document_url, created_at=updated.created_at,
            items=[PolicyItemOut.model_validate(i) for i in updated.items],
        ),
        message="保單已更新",
    )


@router.delete("/policies/{policy_id}")
async def admin_delete_policy(
    policy_id: str,
    admin: AdminUser = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """刪除保單"""
    from app.services.policy_service import PolicyService
    policy = await _resolve_policy_with_perm(db, admin, policy_id)
    pn = policy.policy_number
    svc = PolicyService(db)
    await svc.delete_policy(policy.user_id, policy_id)
    await db.commit()
    await log_action(db, admin, "delete", "policy", policy_id, detail=f"policy_number={pn}")
    return APIResponse(message="保單已刪除")


@router.post("/policies/upload-scan")
async def admin_upload_policy_scan(
    file: UploadFile = File(..., description="保單圖片或 PDF"),
    admin: AdminUser = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """上傳保單圖片（不指定客戶；後續 OCR 時再指定）"""
    import uuid as _uuid
    from pathlib import Path as _P
    from app.config import settings as _s
    from app.core.pdf_utils import is_pdf, pdf_to_images

    allowed = ("image/jpeg", "image/png", "image/webp", "application/pdf")
    if file.content_type not in allowed:
        raise BadRequestError("僅支援 JPG/PNG/WebP/PDF 格式")

    ext = file.filename.rsplit(".", 1)[-1] if file.filename else "jpg"
    filename = f"policy_{_uuid.uuid4().hex[:8]}.{ext}"
    upload_dir = _P(_s.UPLOAD_DIR) / "policies"
    upload_dir.mkdir(parents=True, exist_ok=True)
    filepath = upload_dir / filename
    content = await file.read()
    filepath.write_bytes(content)

    image_name = filename
    if is_pdf(file.content_type, file.filename):
        images = pdf_to_images(str(filepath), str(upload_dir))
        if images:
            image_name = _P(images[0]).name

    await log_action(db, admin, "upload", "policy_scan", detail=image_name)
    return APIResponse(
        data={"image_url": f"/uploads/policies/{image_name}", "filename": image_name},
        message="保單已上傳，請選擇客戶並執行 AI 辨識",
    )


@router.post("/customer/{customer_id}/policies/ocr-scan")
async def admin_ocr_policy_scan(
    customer_id: str,
    filename: str = Query(..., description="上傳後的檔名"),
    admin: AdminUser = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """對已上傳的保單圖片 OCR 並掛在指定客戶名下"""
    from pathlib import Path as _P
    from datetime import date as _date, timedelta
    import uuid as _uuid
    from app.config import settings as _s
    from app.core.ocr_policy import analyze_policy
    from app.schemas.policy import PolicyCreate, PolicyItemCreate, PolicyDetailOut, PolicyItemOut
    from app.services.policy_service import PolicyService

    await _check_customer_perm(db, admin, customer_id)

    upload_dir = _P(_s.UPLOAD_DIR) / "policies"
    image_path = str(upload_dir / filename)
    if not _P(image_path).exists():
        raise BadRequestError("找不到上傳的保單圖片")

    ocr_result = await analyze_policy(image_path)

    policy_created = None
    if ocr_result and "error" not in ocr_result:
        try:
            items_data = []
            for item in ocr_result.get("items", []):
                if item.get("item_name"):
                    items_data.append(PolicyItemCreate(
                        item_name=item["item_name"],
                        coverage_limit=item.get("coverage_limit"),
                        deductible=item.get("deductible"),
                        premium=item.get("premium"),
                    ))

            start, end = None, None
            try:
                if ocr_result.get("start_date"):
                    start = _date.fromisoformat(ocr_result["start_date"])
                if ocr_result.get("end_date"):
                    end = _date.fromisoformat(ocr_result["end_date"])
            except (ValueError, TypeError):
                pass
            if not start: start = _date.today()
            if not end: end = start + timedelta(days=365)

            vehicle_id = None
            if ocr_result.get("plate_number"):
                vr = await db.execute(
                    select(UserVehicle).where(
                        UserVehicle.user_id == customer_id,
                        UserVehicle.plate_number == ocr_result["plate_number"],
                    )
                )
                veh = vr.scalar_one_or_none()
                if veh:
                    vehicle_id = veh.id

            policy_data = PolicyCreate(
                insurer_name=ocr_result.get("insurer_name") or "未辨識",
                policy_number=ocr_result.get("policy_number") or f"SCAN-{_uuid.uuid4().hex[:8].upper()}",
                vehicle_id=vehicle_id, status="active",
                start_date=start, end_date=end,
                total_premium=ocr_result.get("total_premium"),
                document_url=f"/uploads/policies/{filename}",
                items=items_data,
            )
            svc = PolicyService(db)
            policy_created = await svc.create_policy(customer_id, policy_data)
            await db.commit()
        except Exception as e:
            ocr_result["_create_error"] = str(e)

    has_ocr = ocr_result and "error" not in ocr_result
    await log_action(db, admin, "ocr", "policy_scan", customer_id, detail=filename)
    return APIResponse(
        data={
            "ocr_result": ocr_result if has_ocr else None,
            "ocr_available": has_ocr,
            "policy": PolicyDetailOut(
                id=policy_created.id, insurer_name=policy_created.insurer_name,
                policy_number=policy_created.policy_number, status=policy_created.status,
                start_date=policy_created.start_date, end_date=policy_created.end_date,
                total_premium=policy_created.total_premium, days_remaining=0,
                document_url=policy_created.document_url, created_at=policy_created.created_at,
                items=[PolicyItemOut.model_validate(i) for i in policy_created.items],
            ) if policy_created else None,
        },
        message="AI 辨識完成" if policy_created else (f"辨識完成但建立失敗" if has_ocr else "辨識失敗"),
    )


# ═══════════════════════════════════════════════════
# 業務員手動推播 LINE 訊息給客戶（業務員主動關懷）
# ═══════════════════════════════════════════════════

class PushToCustomerRequest(BaseModel):
    customer_id: str
    message: str  # 純文字，最多 5000 字
    title: str | None = None  # 可選標題（會以 emoji+標題開頭）


@router.post("/line/push-to-customer")
async def push_to_customer(
    req: PushToCustomerRequest,
    admin: AdminUser = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """
    業務員主動推播訊息給指定客戶（會檢查客戶是否符合推播條件）。
    - agent 只能推播給自己分配的客戶
    - super_admin 可推播給任何客戶
    - 會自動加上 BOPINAN 品牌前綴
    """
    from app.core.line_messaging import line_messaging, can_push_to

    if not req.message or len(req.message.strip()) == 0:
        raise BadRequestError("訊息內容不可為空")
    if len(req.message) > 4500:
        raise BadRequestError("訊息超過 4500 字（LINE 限制 5000）")

    # 權限檢查
    accessible = await get_accessible_customer_ids(admin, db)
    if accessible is not None and req.customer_id not in accessible:
        raise ForbiddenError("無權限推播給此客戶")

    res = await db.execute(select(User).where(User.id == req.customer_id))
    user = res.scalar_one_or_none()
    if not user:
        raise NotFoundError("客戶不存在")

    if not can_push_to(user):
        reason = "未綁定 LINE" if not user.line_user_id else (
            "未加 BOPINAN OA 好友" if not user.is_line_friend else "已關閉 LINE 通知"
        )
        return APIResponse(success=False, message=f"無法推播：{reason}")

    if req.title:
        full_msg = f"🛡 BOPINAN {req.title}\n\n{req.message}\n\n— {admin.display_name or admin.username}"
    else:
        full_msg = f"🛡 BOPINAN\n\n{req.message}\n\n— {admin.display_name or admin.username}"

    sent = await line_messaging.send_text(user.line_user_id, full_msg)
    await log_action(db, admin, "push", "line_message", req.customer_id,
                     detail=req.message[:100])
    await db.commit()

    return APIResponse(
        success=sent,
        data={"customer_name": user.name, "message_preview": req.message[:50]},
        message="推播成功" if sent else "推播失敗（看 Render log）",
    )


# ═══════════════════════════════════════════════════
# 極簡 LINE 推播測試（不需要建 claim）
# ═══════════════════════════════════════════════════

@router.post("/line/test-push-first")
async def test_line_push_first(
    admin: AdminUser = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """
    自動找第一個符合推播條件的用戶（line_user_id + is_line_friend + line_notify_enabled），
    傳一則測試訊息。最快驗證 LINE 推播管道。
    """
    from app.core.line_messaging import line_messaging
    from datetime import datetime
    from zoneinfo import ZoneInfo

    res = await db.execute(
        select(User).where(
            User.line_user_id.isnot(None),
            User.is_line_friend == True,  # noqa: E712
            User.line_notify_enabled == True,  # noqa: E712
        ).limit(1)
    )
    user = res.scalar_one_or_none()
    if not user:
        return APIResponse(
            success=False,
            message="DB 沒有任何符合條件的用戶（需 line_user_id + is_line_friend=True + line_notify_enabled=True）",
        )

    now = datetime.now(ZoneInfo("Asia/Taipei")).strftime("%m/%d %H:%M")
    msg = (
        f"🛡 BOPINAN 測試推播\n\n"
        f"哈囉 {user.name or '客戶'}，這是 admin 觸發的測試訊息。\n"
        f"如果您看到這則訊息，代表 BOPINAN ↔ LINE 推播管道暢通。\n\n"
        f"時間：{now}\n"
        f"觸發者：{admin.username}"
    )
    sent = await line_messaging.send_text(user.line_user_id, msg)
    return APIResponse(
        success=sent,
        data={"name": user.name, "user_id": user.id, "line_user_prefix": user.line_user_id[:10] + "..."},
        message="推播成功，請看您手機 LINE" if sent else "推播失敗（看 Render log 找原因）",
    )


@router.post("/line/test-push")
async def test_line_push(
    email: str = Query(..., description="收件用戶的 email（該用戶必須已綁定 LINE 並加 OA 好友）"),
    admin: AdminUser = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """
    一鍵測試 LINE 推播：填收件用戶的 email，秒推一則測試訊息。
    用來驗證 LINE Messaging API 串接是否正常。
    """
    from app.core.line_messaging import line_messaging
    from datetime import datetime
    from zoneinfo import ZoneInfo

    res = await db.execute(select(User).where(User.email == email))
    user = res.scalar_one_or_none()
    if not user:
        return APIResponse(success=False, message=f"找不到 email={email} 的用戶")
    if not user.line_user_id:
        return APIResponse(success=False, message="該用戶未綁定 LINE（需先用 LINE 登入過 BOPINAN）")
    if not user.is_line_friend:
        return APIResponse(success=False, message="該用戶未加 BOPINAN OA 好友")
    if not user.line_notify_enabled:
        return APIResponse(success=False, message="該用戶已關閉 LINE 通知")

    now = datetime.now(ZoneInfo("Asia/Taipei")).strftime("%m/%d %H:%M")
    msg = (
        f"🛡 BOPINAN 測試推播\n\n"
        f"哈囉 {user.name or '客戶'}，這是 admin 觸發的測試訊息。\n"
        f"如果您看到這則訊息，代表 BOPINAN ↔ LINE 推播管道暢通。\n\n"
        f"時間：{now}\n"
        f"觸發者：{admin.username}"
    )
    sent = await line_messaging.send_text(user.line_user_id, msg)
    return APIResponse(
        success=sent,
        data={"sent_to": user.line_user_id[:10] + "...", "name": user.name},
        message="推播成功，請看您手機 LINE" if sent else "推播失敗（看 Render log 找原因）",
    )


# ═══════════════════════════════════════════════════
# 理賠案件列表 + 進度管理（觸發 LINE 推播）
# ═══════════════════════════════════════════════════

@router.get("/all/claims")
async def get_all_claims(
    status: str | None = Query(None, description="可選：filter by status"),
    admin: AdminUser = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """
    列出可存取的全部理賠案件（含客戶資訊 + LINE 推播資格）。
    line_can_push=true 代表呼叫 progress endpoint 會觸發 LINE 推播給該客戶。
    """
    from app.models.claim import ClaimAdjuster
    from app.services.claim_service import STAGE_LABELS

    accessible = await get_accessible_customer_ids(admin, db)
    query = (
        select(Claim)
        .options(selectinload(Claim.user), selectinload(Claim.adjuster))
    )
    if accessible is not None:
        query = query.where(Claim.user_id.in_(accessible))
    if status:
        query = query.where(Claim.status == status)
    query = query.order_by(Claim.submitted_at.desc())

    result = await db.execute(query)
    rows = []
    for c in result.scalars().all():
        u = c.user
        line_can_push = bool(
            u and u.line_user_id and u.is_line_friend and u.line_notify_enabled
        )
        rows.append({
            "id": c.id,
            "claim_number": c.claim_number,
            "status": c.status,
            "status_label": STAGE_LABELS.get(c.status, c.status),
            "claim_type": c.claim_type,
            "claimed_amount": float(c.claimed_amount) if c.claimed_amount else None,
            "approved_amount": float(c.approved_amount) if c.approved_amount else None,
            "submitted_at": c.submitted_at.isoformat() if c.submitted_at else None,
            "resolved_at": c.resolved_at.isoformat() if c.resolved_at else None,
            "user_id": c.user_id,
            "customer_name": u.name if u else None,
            "customer_email": u.email if u else None,
            "customer_phone": u.phone if u else None,
            "line_can_push": line_can_push,
            "line_bound": bool(u and u.line_user_id),
            "is_line_friend": bool(u and u.is_line_friend),
            "line_notify_enabled": bool(u and u.line_notify_enabled),
            "adjuster_name": c.adjuster.adjuster_name if c.adjuster else None,
            "policy_id": c.policy_id,
            "notes": (c.notes or "")[:200],
        })
    await log_action(db, admin, "view", "all_claims", detail=f"{len(rows)} 筆")
    return APIResponse(data=rows)


class ClaimProgressUpdate(BaseModel):
    stage: str  # submitted/reviewing/investigating/negotiating/approved/paying/closed
    description: str


@router.post("/claims/{claim_id}/progress")
async def update_claim_progress(
    claim_id: str,
    req: ClaimProgressUpdate,
    admin: AdminUser = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """
    更新理賠案件進度，自動推播 LINE 通知（若用戶已加好友且未關閉）。
    Admin agent 只能改自己的客戶的案件。
    """
    from app.services.claim_service import ClaimService, CLAIM_STAGES

    if req.stage not in CLAIM_STAGES:
        raise BadRequestError(f"stage 必須為以下其中之一：{', '.join(CLAIM_STAGES)}")

    res = await db.execute(select(Claim).where(Claim.id == claim_id))
    claim = res.scalar_one_or_none()
    if not claim:
        raise NotFoundError("理賠案件不存在")

    # 權限檢查：agent 只能改自己客戶的案件
    accessible = await get_accessible_customer_ids(admin, db)
    if accessible is not None and claim.user_id not in accessible:
        raise ForbiddenError("無權限修改此案件")

    svc = ClaimService(db)
    updated = await svc.update_progress(
        claim_id=claim_id,
        new_stage=req.stage,
        description=req.description,
        changed_by=admin.username,
    )
    await log_action(db, admin, "update", "claim_progress", claim_id,
                     detail=f"{req.stage}: {req.description[:50]}")
    await db.commit()

    # commit 成功後才推播，避免 rollback 後發出幽靈通知
    await svc.notify_progress(updated, req.stage, req.description)

    return APIResponse(data={
        "claim_id": updated.id,
        "claim_number": updated.claim_number,
        "status": updated.status,
    }, message="進度已更新並推播")

from datetime import date, timedelta, datetime, timezone
from fastapi import APIRouter, Depends, Query
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from app.dependencies import get_db, get_current_user
from app.models.user import User
from app.models.policy import Policy, PolicyItem
from app.models.vehicle import UserVehicle
from app.schemas.notification import NotificationOut
from app.schemas.common import APIResponse
from app.services.notification_service import NotificationService

router = APIRouter()


def _compute_next_inspection(year: int, vehicle_type: str, today: date) -> dict | None:
    """
    依車齡和車輛型式推算下次驗車日。
    台灣監理規則：
      自用小客車/小貨車：5年內免驗 → 5~10年每年1次 → 10年以上每年2次(每6月)
      營業小客車(計程車)：每年1次 → 5年以上每年2次
      營業大客車/遊覽車：每年3次(每4月)
      營業大貨車：每年2次(每6月)
      機車：5年內免驗 → 5年以上每年1次
    """
    car_age = today.year - year
    if car_age < 0:
        return None

    vt = vehicle_type or ""
    rule = ""

    # 判斷驗車頻率（月數）
    if "營業大客" in vt or "遊覽" in vt:
        interval_months = 4
        rule = "營業大客車每4個月驗車1次"
    elif "營業大貨" in vt:
        interval_months = 6
        rule = "營業大貨車每6個月驗車1次"
    elif "營業小客" in vt or "計程" in vt:
        if car_age >= 5:
            interval_months = 6
            rule = f"車齡{car_age}年，營業小客車5年以上每6個月驗車1次"
        else:
            interval_months = 12
            rule = f"車齡{car_age}年，營業小客車每年驗車1次"
    elif "大型重機" in vt or "重型機車" in vt or "輕型機車" in vt or "機車" in vt:
        if car_age < 5:
            return {"next_date": date(year + 5, today.month, today.day), "rule": f"車齡{car_age}年，機車5年內免驗"}
        interval_months = 12
        rule = f"車齡{car_age}年，機車5年以上每年驗車1次"
    else:
        # 自用小客車/小貨車（預設）
        if car_age < 5:
            return {"next_date": date(year + 5, today.month, today.day), "rule": f"車齡{car_age}年，自用車5年內免驗"}
        elif car_age < 10:
            interval_months = 12
            rule = f"車齡{car_age}年，5~10年每年驗車1次"
        else:
            interval_months = 6
            rule = f"車齡{car_age}年，10年以上每6個月驗車1次"

    # 從今年初開始算最近的下次驗車日
    from dateutil.relativedelta import relativedelta
    base = date(today.year, 1, 1)
    candidates = []
    for i in range(24):  # 往前後找 2 年
        d = base + relativedelta(months=interval_months * i)
        if d >= today - timedelta(days=30):
            candidates.append(d)
            break
    if candidates:
        return {"next_date": candidates[0], "rule": rule}

    # fallback
    next_d = today + timedelta(days=interval_months * 30)
    return {"next_date": next_d, "rule": rule}


async def _build_pinned_alerts(user_id: str, db: AsyncSession) -> list[dict]:
    """
    永遠置頂：每台車的保單有效期間 + 驗車時間（依車號分組）。
    """
    today = date.today()
    now_iso = datetime.now(timezone.utc).isoformat()
    pinned = []

    # 取所有車輛
    vehicle_result = await db.execute(
        select(UserVehicle).where(UserVehicle.user_id == user_id)
    )
    vehicles = list(vehicle_result.scalars().all())

    for v in vehicles:
        plate = v.plate_number
        car_desc = f"{v.brand or ''} {v.model or ''}".strip() or plate
        car_age = (today.year - v.year) if v.year else None

        # ── 該車所有保單 ──
        pol_result = await db.execute(
            select(Policy).options(selectinload(Policy.items)).where(
                and_(Policy.user_id == user_id, Policy.vehicle_id == v.id)
            ).order_by(Policy.end_date.desc())
        )
        all_policies = list(pol_result.scalars().all())

        policy_lines = []
        has_comp = False
        comp_expiry = None
        has_vol = False
        vol_expiry = None
        min_policy_days = 9999
        for p in all_policies:
            if p.status not in ("active", "expiring") or p.end_date < today:
                continue
            pd = (p.end_date - today).days
            if pd < min_policy_days:
                min_policy_days = pd
            policy_lines.append(
                f"{p.insurer_name} {p.policy_number}  "
                f"{p.start_date.strftime('%Y/%m/%d')}~{p.end_date.strftime('%Y/%m/%d')}（剩 {pd} 天）"
            )
            for item in p.items:
                if not item.is_active:
                    continue
                if "強制" in item.item_name:
                    has_comp = True
                    if comp_expiry is None or p.end_date > comp_expiry:
                        comp_expiry = p.end_date
                else:
                    # 非強制險 = 任意險（第三人、車體、竊盜、超額等）
                    has_vol = True
                    if vol_expiry is None or p.end_date > vol_expiry:
                        vol_expiry = p.end_date

        if not policy_lines:
            policy_lines.append("無有效保單")

        comp_days = (comp_expiry - today).days if comp_expiry else 0
        comp_ok = has_comp and comp_days >= 30
        vol_days = (vol_expiry - today).days if vol_expiry else 0
        if has_comp:
            comp_line = f"有效至 {comp_expiry.strftime('%Y/%m/%d')}（剩 {comp_days} 天）"
            if not comp_ok:
                comp_line += " — 不足30天，無法驗車"
        else:
            comp_line = "未投保，無法驗車"

        # ── 驗車時間（行照到期日 or 依車齡推算）──
        insp_days = 9999
        if v.registration_expiry:
            insp_expiry = v.registration_expiry
            insp_source = ""
        elif v.year:
            computed = _compute_next_inspection(v.year, v.vehicle_type or "", today)
            if computed:
                insp_expiry = computed["next_date"]
                insp_source = computed["rule"]
            else:
                insp_expiry = None
                insp_source = ""
        else:
            insp_expiry = None
            insp_source = ""

        if insp_expiry:
            insp_days = (insp_expiry - today).days
            ws = (insp_expiry - timedelta(days=30)).strftime("%Y/%m/%d")
            we = (insp_expiry + timedelta(days=30)).strftime("%Y/%m/%d")
            if insp_days < 0:
                insp_line = f"{insp_expiry.strftime('%Y/%m/%d')}（已逾期 {abs(insp_days)} 天）"
            elif insp_days == 0:
                insp_line = f"{insp_expiry.strftime('%Y/%m/%d')}（今日到期）"
            else:
                insp_line = f"{insp_expiry.strftime('%Y/%m/%d')}（倒數 {insp_days} 天）"
            insp_line += f"\n     可驗車區間 {ws} ~ {we}"
            if insp_source:
                insp_line += f"\n     {insp_source}"
        else:
            insp_line = "未設定"

        # ── 緊急度 ──
        urgency = "info"
        sort_key = min(insp_days, min_policy_days)
        if insp_days < 0 or min_policy_days < 0:
            urgency = "overdue"
        elif insp_days <= 30 or min_policy_days <= 30:
            urgency = "urgent"
        elif insp_days <= 60 or min_policy_days <= 60:
            urgency = "upcoming"

        # ── 可否驗車判斷 ──
        in_window = False
        can_inspect = False
        window_status = ""
        if insp_expiry:
            in_window = -30 <= insp_days <= 30
            can_inspect = in_window and comp_ok
            if insp_days < -30:
                window_status = "已超過可驗車期限"
            elif insp_days < 0:
                window_status = f"逾期中，尚可驗車（剩 {30 + insp_days} 天）"
            elif insp_days <= 30:
                window_status = "已進入可驗車區間"
            else:
                window_status = f"尚未到可驗車期間（{30 - insp_days + insp_days} 天後開始）" if insp_days <= 60 else "尚未到期"

        pinned.append({
            "id": f"_pin_{v.id}",
            "title": f"{plate}",
            "notification_type": "pinned_vehicle",
            "reference_type": "vehicle",
            "reference_id": v.id,
            "is_read": False,
            "is_pinned": True,
            "urgency": urgency,
            "days_left": sort_key,
            "sent_at": now_iso,
            "created_at": now_iso,
            # 結構化資料供前端三區顯示
            "vehicle": {
                "plate": plate,
                "desc": car_desc,
                "car_age": car_age,
            },
            "zone_policy": {
                "policies": policy_lines,
                "compulsory": {
                    "has": has_comp,
                    "expiry": comp_expiry.strftime("%Y/%m/%d") if comp_expiry else None,
                    "days": comp_days,
                    "ok_for_inspect": comp_ok,
                },
                "voluntary": {
                    "has": has_vol,
                    "expiry": vol_expiry.strftime("%Y/%m/%d") if vol_expiry else None,
                    "days": vol_days,
                },
            },
            "zone_inspection": {
                "expiry": insp_expiry.strftime("%Y/%m/%d") if insp_expiry else None,
                "days_left": insp_days if insp_days < 9999 else None,
                "window_start": (insp_expiry - timedelta(days=30)).strftime("%Y/%m/%d") if insp_expiry else None,
                "window_end": (insp_expiry + timedelta(days=30)).strftime("%Y/%m/%d") if insp_expiry else None,
                "source": insp_source,
            },
            "zone_can_inspect": {
                "in_window": in_window,
                "can_inspect": can_inspect,
                "window_status": window_status,
                "reasons": (
                    [] if can_inspect else
                    ([f"強制險剩餘 {comp_days} 天，不足 30 天" if has_comp and not comp_ok else "無強制險"] if not comp_ok else []) +
                    (["未到可驗車區間"] if not in_window and insp_expiry and insp_days > 30 else []) +
                    (["已超過可驗車期限"] if insp_expiry and insp_days < -30 else [])
                ),
            },
            # 向下相容的 body（給一般通知列表用）
            "body": f"{car_desc} {plate}" + (f" 車齡{car_age}年" if car_age else ""),
        })

    order = {"overdue": 0, "urgent": 1, "upcoming": 2, "info": 3}
    pinned.sort(key=lambda x: (order.get(x["urgency"], 9), x["days_left"]))
    return pinned


@router.get("", response_model=APIResponse)
async def list_notifications(
    unread_only: bool = Query(False),
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=50),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """取得通知列表（純一般通知，保單/驗車改由首頁顯示）"""
    svc = NotificationService(db)
    notifications, total = await svc.list_notifications(current_user.id, unread_only, page, per_page)
    regular = [NotificationOut.model_validate(n) for n in notifications]

    return APIResponse(data={
        "pinned": [],
        "items": [n.model_dump() for n in regular],
        "total": total,
        "page": page,
        "per_page": per_page,
        "unread_count": await svc.get_unread_count(current_user.id),
    })


@router.get("/vehicles-status", response_model=APIResponse)
async def vehicles_status(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """首頁用：每台車的保單+驗車狀態"""
    data = await _build_pinned_alerts(current_user.id, db)
    return APIResponse(data=data)


@router.patch("/{notification_id}/read", response_model=APIResponse)
async def mark_read(
    notification_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """標記已讀"""
    svc = NotificationService(db)
    await svc.mark_read(current_user.id, notification_id)
    return APIResponse(message="已標記為已讀")


@router.patch("/read-all", response_model=APIResponse)
async def mark_all_read(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """全部標記已讀"""
    svc = NotificationService(db)
    count = await svc.mark_all_read(current_user.id)
    return APIResponse(message=f"已將 {count} 則通知標記為已讀")

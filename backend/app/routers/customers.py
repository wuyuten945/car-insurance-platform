from pathlib import Path
from fastapi import APIRouter, Depends, UploadFile, File
from sqlalchemy import select, update as sa_update
from sqlalchemy.ext.asyncio import AsyncSession
from app.dependencies import get_db, get_current_user
from app.models.user import User, UserConsent
from app.models.vehicle import UserVehicle
from app.models.policy import Policy
from app.models.accident import Accident
from app.models.claim import Claim
from app.models.notification import Notification
from app.schemas.user import UserOut, UserProfileUpdate, ConsentUpdate, ConsentOut, VehicleCreate, VehicleUpdate, VehicleOut
from app.schemas.common import APIResponse
from app.services.user_service import UserService
from app.exceptions import BadRequestError, NotFoundError

router = APIRouter()


@router.get("/profile", response_model=APIResponse)
async def get_profile(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """取得個人資料"""
    return APIResponse(data=UserOut.model_validate(current_user))


@router.patch("/profile", response_model=APIResponse)
async def update_profile(
    data: UserProfileUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """更新個人資料"""
    svc = UserService(db)
    user = await svc.update_profile(current_user.id, data)
    return APIResponse(data=UserOut.model_validate(user), message="資料已更新")


@router.get("/line/status", response_model=APIResponse)
async def line_status(
    current_user: User = Depends(get_current_user),
):
    """取得目前 LINE 綁定狀態 + 官方帳號 ID（給前端顯示「加好友」連結）"""
    from app.config import settings
    return APIResponse(data={
        "bound": bool(current_user.line_user_id),
        "notify_enabled": current_user.line_notify_enabled,
        "is_friend": bool(current_user.is_line_friend),  # 是否已加 OA 好友（沒加無法 push）
        "official_id": settings.LINE_OFFICIAL_ID,
    })


@router.patch("/line/notify", response_model=APIResponse)
async def toggle_line_notify(
    enabled: bool,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """開關 LINE 推播通知"""
    current_user.line_notify_enabled = enabled
    await db.commit()
    return APIResponse(data={"notify_enabled": enabled},
                       message="LINE 通知已" + ("開啟" if enabled else "關閉"))


@router.delete("/line/unbind", response_model=APIResponse)
async def unbind_line(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """解除 LINE 綁定"""
    current_user.line_user_id = None
    await db.commit()
    return APIResponse(message="已解除 LINE 綁定")


def _mask_phone(phone: str) -> str:
    """0952156100 → 0952-XXX-100（中段隱藏）"""
    if not phone or len(phone) < 7:
        return phone or ""
    return f"{phone[:4]}-XXX-{phone[-3:]}"


@router.get("/profile/match-existing", response_model=APIResponse)
async def match_existing_account(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """查找是否有業務員預先建立的同一身份證帳號（OAuth 自助登入後使用）。

    比對方式：以當前用戶的 id_number_hash 找其他不同 user.id 但 hash 相同的帳號。
    回傳遮罩後的 phone 提示，不回傳 user_id（避免被攻擊者枚舉）。
    """
    if not current_user.id_number_hash:
        return APIResponse(data={"matched": False, "reason": "尚未填寫身份證字號，無法比對"})

    result = await db.execute(
        select(User).where(
            User.id_number_hash == current_user.id_number_hash,
            User.id != current_user.id,
        )
    )
    matches = result.scalars().all()
    if not matches:
        return APIResponse(data={"matched": False})

    # 取最早建立的那筆（業務員 import 的通常較早）
    matches.sort(key=lambda u: u.created_at or 0)
    target = matches[0]

    return APIResponse(data={
        "matched": True,
        "masked_phone": _mask_phone(target.phone or ""),
        "name_hint": (target.name[0] + "○" * (len(target.name) - 1)) if target.name else None,
        "message": "我們找到一筆業務員預先建立的資料，可能屬於您。可一鍵合併到此帳號。",
    })


@router.post("/profile/claim-existing", response_model=APIResponse)
async def claim_existing_account(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """自助合併：把同 id_number_hash 的舊帳號（業務員預先建立）下的車輛/保單/事故/理賠/通知，
    全部移轉到當前登入帳號，並補齊 profile 欄位，最後刪除被合併的舊 user。

    安全前提：必須有 id_number_hash（已通過 onboarding 補資料），且 hash 完全相符。
    """
    if not current_user.id_number_hash:
        raise BadRequestError("請先完成資料填寫（身份證字號）才能合併既有資料")

    result = await db.execute(
        select(User).where(
            User.id_number_hash == current_user.id_number_hash,
            User.id != current_user.id,
        )
    )
    matches = result.scalars().all()
    if not matches:
        raise NotFoundError("找不到可合併的既有資料")

    moved_counts = {"vehicles": 0, "policies": 0, "accidents": 0, "claims": 0, "notifications": 0, "consents": 0}
    merged_ids: list[str] = []

    for old_user in matches:
        old_id = old_user.id

        # 1) 移轉子表 user_id → current_user.id
        for model, key in [
            (UserVehicle, "vehicles"),
            (Policy, "policies"),
            (Accident, "accidents"),
            (Claim, "claims"),
            (Notification, "notifications"),
            (UserConsent, "consents"),
        ]:
            r = await db.execute(
                sa_update(model)
                .where(model.user_id == old_id)
                .values(user_id=current_user.id)
            )
            moved_counts[key] += r.rowcount or 0

        # 2) 補齊 current_user 缺失的 profile 欄位（不覆蓋已填的）
        for field in (
            "name", "birth_date", "address", "registered_address",
            "emergency_contact_name", "emergency_contact_phone", "emergency_contact_relation",
            "license_number", "license_expiry", "avatar_url",
        ):
            if not getattr(current_user, field) and getattr(old_user, field):
                setattr(current_user, field, getattr(old_user, field))

        # phone/email 只在 current_user 沒有 + 不會撞 unique 時補
        if not current_user.phone and old_user.phone:
            dup = await db.execute(
                select(User).where(User.phone == old_user.phone, User.id != current_user.id, User.id != old_id)
            )
            if not dup.scalar_one_or_none():
                current_user.phone = old_user.phone
        if not current_user.email and old_user.email:
            dup = await db.execute(
                select(User).where(User.email == old_user.email, User.id != current_user.id, User.id != old_id)
            )
            if not dup.scalar_one_or_none():
                current_user.email = old_user.email

        # 3) 清空舊 user 的 phone/email（避免 unique 衝突），再刪除
        old_user.phone = None
        old_user.email = None
        await db.flush()
        await db.delete(old_user)
        merged_ids.append(old_id)

    await db.commit()

    return APIResponse(
        data={"merged_user_ids": merged_ids, "moved": moved_counts},
        message=f"已合併 {len(merged_ids)} 筆既有資料：車輛 {moved_counts['vehicles']}、保單 {moved_counts['policies']}",
    )


@router.get("/consents", response_model=APIResponse)
async def get_consents(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """取得個資同意狀態"""
    svc = UserService(db)
    consents = await svc.get_consents(current_user.id)
    return APIResponse(data=[ConsentOut.model_validate(c) for c in consents])


@router.put("/consents", response_model=APIResponse)
async def update_consent(
    data: ConsentUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """更新個資同意狀態"""
    svc = UserService(db)
    consent = await svc.update_consent(current_user.id, data)
    return APIResponse(data=ConsentOut.model_validate(consent), message="同意設定已更新")


# Vehicles
@router.get("/vehicles", response_model=APIResponse)
async def list_vehicles(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """取得車輛列表"""
    svc = UserService(db)
    vehicles = await svc.list_vehicles(current_user.id)
    return APIResponse(data=[VehicleOut.model_validate(v) for v in vehicles])


@router.post("/vehicles", response_model=APIResponse)
async def create_vehicle(
    data: VehicleCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """新增車輛"""
    svc = UserService(db)
    vehicle = await svc.create_vehicle(current_user.id, data)
    return APIResponse(data=VehicleOut.model_validate(vehicle), message="車輛已新增")


@router.put("/vehicles/{vehicle_id}", response_model=APIResponse)
async def update_vehicle(
    vehicle_id: str,
    data: VehicleCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """更新車輛"""
    svc = UserService(db)
    vehicle = await svc.update_vehicle(current_user.id, vehicle_id, data)
    return APIResponse(data=VehicleOut.model_validate(vehicle), message="車輛已更新")


@router.patch("/vehicles/{vehicle_id}", response_model=APIResponse)
async def patch_vehicle(
    vehicle_id: str,
    data: VehicleUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """部分更新車輛（行照日期等）"""
    svc = UserService(db)
    vehicle = await svc.patch_vehicle(current_user.id, vehicle_id, data)
    return APIResponse(data=VehicleOut.model_validate(vehicle), message="車輛已更新")


@router.delete("/vehicles/{vehicle_id}", response_model=APIResponse)
async def delete_vehicle(
    vehicle_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """刪除車輛"""
    svc = UserService(db)
    await svc.delete_vehicle(current_user.id, vehicle_id)
    return APIResponse(message="車輛已刪除")


@router.post("/vehicles/{vehicle_id}/registration", response_model=APIResponse)
async def upload_registration(
    vehicle_id: str,
    file: UploadFile = File(..., description="行照圖片或 PDF"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """上傳行照（JPG/PNG/PDF，立即回應，不等 OCR）"""
    svc = UserService(db)
    vehicle = await svc.upload_registration(current_user.id, vehicle_id, file)

    return APIResponse(
        data={
            "vehicle": VehicleOut.model_validate(vehicle),
            "ocr_result": None,
            "ocr_available": False,
        },
        message="行照已上傳成功，請手動填寫車輛資料或點擊 AI 辨識",
    )


@router.post("/vehicles/{vehicle_id}/ocr", response_model=APIResponse)
async def ocr_registration(
    vehicle_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """對已上傳的行照執行 AI OCR 辨識（獨立呼叫，避免上傳等待）"""
    from app.core.ocr_registration import analyze_registration
    from app.config import settings as _s

    svc = UserService(db)
    # 取得車輛
    from sqlalchemy import select, and_
    from app.models.vehicle import UserVehicle as _UV
    result = await db.execute(select(_UV).where(and_(_UV.id == vehicle_id, _UV.user_id == current_user.id)))
    vehicle = result.scalar_one_or_none()
    if not vehicle or not vehicle.registration_image_url:
        from app.exceptions import BadRequestError
        raise BadRequestError("請先上傳行照圖片")

    image_path = str(Path(_s.UPLOAD_DIR) / "registrations" / Path(vehicle.registration_image_url).name)
    if not Path(image_path).exists():
        image_path = str((Path(_s.UPLOAD_DIR) / vehicle.registration_image_url.lstrip("/uploads/")).resolve())

    ocr_result = await analyze_registration(image_path)

    if ocr_result and "error" not in ocr_result:
        from datetime import date as _date
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
        await db.flush()

    has_ocr = ocr_result and "error" not in ocr_result
    return APIResponse(
        data={
            "vehicle": VehicleOut.model_validate(vehicle),
            "ocr_result": ocr_result if has_ocr else None,
            "ocr_available": has_ocr,
        },
        message="AI 辨識完成，資料已自動填入" if has_ocr else f"辨識失敗: {ocr_result.get('error','')}",
    )


@router.get("/vehicles/{vehicle_id}/inspection-status", response_model=APIResponse)
async def get_inspection_status(
    vehicle_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """查詢車輛驗車狀態（含強制險檢查）"""
    svc = UserService(db)
    status = await svc.get_inspection_status(current_user.id, vehicle_id)
    return APIResponse(data=status)

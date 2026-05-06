import uuid
from pathlib import Path
from fastapi import APIRouter, Depends, Query, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import date
from app.dependencies import get_db, get_current_user
from app.models.user import User
from app.config import settings
from app.schemas.policy import (
    PolicyOut, PolicyItemOut, PolicyDetailOut, ExclusionListOut,
    PaymentMethodOut, PaymentMethodCreate,
    PolicyCreate, PolicyUpdate, PolicyItemCreate, PolicyItemUpdate,
)
from app.schemas.common import APIResponse
from app.services.policy_service import PolicyService

router = APIRouter()


# ===== Static paths FIRST (before /{policy_id} wildcard) =====

# ===== Policy Image Upload + OCR =====

@router.post("/upload-scan", response_model=APIResponse)
async def upload_policy_scan(
    file: UploadFile = File(..., description="保單圖片或 PDF"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """上傳保單（JPG/PNG/PDF）— 立即回應，不等 OCR"""
    from app.core.pdf_utils import is_pdf, pdf_to_images

    allowed = ("image/jpeg", "image/png", "image/webp", "application/pdf")
    if file.content_type not in allowed:
        from app.exceptions import BadRequestError
        raise BadRequestError("僅支援 JPG/PNG/WebP/PDF 格式")

    ext = file.filename.rsplit(".", 1)[-1] if file.filename else "jpg"
    filename = f"policy_{uuid.uuid4().hex[:8]}.{ext}"
    upload_dir = Path(settings.UPLOAD_DIR) / "policies"
    upload_dir.mkdir(parents=True, exist_ok=True)
    filepath = upload_dir / filename
    content = await file.read()
    filepath.write_bytes(content)

    # PDF → 轉第一頁為 JPG
    image_name = filename
    if is_pdf(file.content_type, file.filename):
        images = pdf_to_images(str(filepath), str(upload_dir))
        if images:
            image_name = Path(images[0]).name

    return APIResponse(
        data={"image_url": f"/uploads/policies/{image_name}", "filename": image_name},
        message="保單已上傳成功，請點 AI 辨識或手動建立",
    )


@router.post("/ocr-scan", response_model=APIResponse)
async def ocr_policy_scan(
    filename: str = Query(..., description="上傳後的檔名"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """對已上傳的保單圖片執行 AI OCR 辨識並自動建立保單"""
    upload_dir = Path(settings.UPLOAD_DIR) / "policies"
    image_path = str(upload_dir / filename)
    if not Path(image_path).exists():
        from app.exceptions import BadRequestError
        raise BadRequestError("找不到上傳的保單圖片")

    from app.core.ocr_policy import analyze_policy
    ocr_result = await analyze_policy(image_path)

    policy_created = None
    if ocr_result and "error" not in ocr_result:
        try:
            from datetime import date as _date, timedelta
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
                from sqlalchemy import select
                from app.models.vehicle import UserVehicle
                vr = await db.execute(
                    select(UserVehicle).where(
                        UserVehicle.user_id == current_user.id,
                        UserVehicle.plate_number == ocr_result["plate_number"],
                    )
                )
                veh = vr.scalar_one_or_none()
                if veh: vehicle_id = veh.id

            policy_data = PolicyCreate(
                insurer_name=ocr_result.get("insurer_name") or "未辨識",
                policy_number=ocr_result.get("policy_number") or f"SCAN-{uuid.uuid4().hex[:8].upper()}",
                vehicle_id=vehicle_id, status="active",
                start_date=start, end_date=end,
                total_premium=ocr_result.get("total_premium"),
                document_url=f"/uploads/policies/{filename}",
                items=items_data,
            )
            svc = PolicyService(db)
            policy_created = await svc.create_policy(current_user.id, policy_data)
        except Exception as e:
            ocr_result["_create_error"] = str(e)

    has_ocr = ocr_result and "error" not in ocr_result
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
        message="AI 辨識完成，保單已自動建立" if policy_created else ("辨識完成但建立失敗" if has_ocr else f"辨識失敗: {ocr_result.get('error','')}"),
    )


# Payment methods
@router.get("/payment-methods", response_model=APIResponse)
async def list_payment_methods(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """取得付款方式"""
    svc = PolicyService(db)
    methods = await svc.list_payment_methods(current_user.id)
    return APIResponse(data=[PaymentMethodOut.model_validate(m) for m in methods])


@router.post("/payment-methods", response_model=APIResponse)
async def create_payment_method(
    data: PaymentMethodCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """新增付款方式"""
    svc = PolicyService(db)
    method = await svc.create_payment_method(current_user.id, data)
    return APIResponse(data=PaymentMethodOut.model_validate(method), message="付款方式已新增")


# ===== Policy list & create =====

@router.get("", response_model=APIResponse)
async def list_policies(
    status: str = Query(None, description="篩選狀態: active, expiring, expired"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """取得保單列表"""
    svc = PolicyService(db)
    policies = await svc.list_policies(current_user.id, status)
    today = date.today()
    result = []
    for p in policies:
        days_remaining = (p.end_date - today).days if p.end_date >= today else 0
        result.append(PolicyOut.model_validate({
            "id": p.id, "insurer_name": p.insurer_name, "policy_number": p.policy_number,
            "status": p.status, "start_date": p.start_date, "end_date": p.end_date,
            "start_time": p.start_time, "end_time": p.end_time,
            "compulsory_insurer_name": p.compulsory_insurer_name,
            "compulsory_policy_number": p.compulsory_policy_number,
            "compulsory_premium": p.compulsory_premium,
            "compulsory_start_date": p.compulsory_start_date,
            "compulsory_end_date": p.compulsory_end_date,
            "compulsory_start_time": p.compulsory_start_time,
            "compulsory_end_time": p.compulsory_end_time,
            "total_premium": p.total_premium, "days_remaining": days_remaining,
            "vehicle_plate": p.vehicle.plate_number if p.vehicle else None,
            "vehicle_brand": p.vehicle.brand if p.vehicle else None,
            "vehicle_model": p.vehicle.model if p.vehicle else None,
            "data_source": p.data_source or "agent",
            "items": [PolicyItemOut.model_validate(i) for i in p.items],
        }))
    return APIResponse(data=result)


@router.post("", response_model=APIResponse)
async def create_policy(
    data: PolicyCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """建立新保單（前台客戶自填，會標記 data_source='self'）"""
    svc = PolicyService(db)
    policy = await svc.create_policy(current_user.id, data, data_source="self")
    today = date.today()
    days_remaining = (policy.end_date - today).days if policy.end_date >= today else 0
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


# ===== Policy detail (wildcard /{policy_id}) =====

@router.get("/{policy_id}", response_model=APIResponse)
async def get_policy(
    policy_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """取得保單詳情"""
    svc = PolicyService(db)
    policy = await svc.get_policy_detail(current_user.id, policy_id)
    today = date.today()
    days_remaining = (policy.end_date - today).days if policy.end_date >= today else 0
    return APIResponse(data=PolicyDetailOut(
        id=policy.id, insurer_name=policy.insurer_name, policy_number=policy.policy_number,
        status=policy.status, start_date=policy.start_date, end_date=policy.end_date,
        total_premium=policy.total_premium, days_remaining=days_remaining,
        document_url=policy.document_url, created_at=policy.created_at,
        items=[PolicyItemOut.model_validate(i) for i in policy.items],
    ))


@router.put("/{policy_id}", response_model=APIResponse)
async def update_policy(
    policy_id: str,
    data: PolicyUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """更新保單（前台只能改自填的紀錄）"""
    svc = PolicyService(db)
    policy = await svc.update_policy(current_user.id, policy_id, data, restrict_to_source="self")
    today = date.today()
    days_remaining = (policy.end_date - today).days if policy.end_date >= today else 0
    return APIResponse(
        data=PolicyDetailOut(
            id=policy.id, insurer_name=policy.insurer_name, policy_number=policy.policy_number,
            status=policy.status, start_date=policy.start_date, end_date=policy.end_date,
            total_premium=policy.total_premium, days_remaining=days_remaining,
            document_url=policy.document_url, created_at=policy.created_at,
            items=[PolicyItemOut.model_validate(i) for i in policy.items],
        ),
        message="保單已更新",
    )


@router.delete("/{policy_id}", response_model=APIResponse)
async def delete_policy(
    policy_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """刪除保單（前台只能刪自填的紀錄）"""
    svc = PolicyService(db)
    await svc.delete_policy(current_user.id, policy_id, restrict_to_source="self")
    return APIResponse(message="保單已刪除")


@router.get("/{policy_id}/exclusions", response_model=APIResponse)
async def get_exclusions(
    policy_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """取得不賠事項"""
    svc = PolicyService(db)
    policy = await svc.get_policy_detail(current_user.id, policy_id)
    exclusions = await svc.get_exclusions(current_user.id, policy_id)
    return APIResponse(data=ExclusionListOut(
        policy_id=policy_id,
        insurer_name=policy.insurer_name,
        exclusions=exclusions,
    ))


# ===== PolicyItem CRUD =====

@router.post("/{policy_id}/items", response_model=APIResponse)
async def add_policy_item(
    policy_id: str,
    data: PolicyItemCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """新增保障項目"""
    svc = PolicyService(db)
    item = await svc.add_policy_item(current_user.id, policy_id, data)
    return APIResponse(data=PolicyItemOut.model_validate(item), message="保障項目已新增")


@router.put("/{policy_id}/items/{item_id}", response_model=APIResponse)
async def update_policy_item(
    policy_id: str,
    item_id: str,
    data: PolicyItemUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """更新保障項目"""
    svc = PolicyService(db)
    item = await svc.update_policy_item(current_user.id, policy_id, item_id, data)
    return APIResponse(data=PolicyItemOut.model_validate(item), message="保障項目已更新")


@router.delete("/{policy_id}/items/{item_id}", response_model=APIResponse)
async def delete_policy_item(
    policy_id: str,
    item_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """刪除保障項目"""
    svc = PolicyService(db)
    await svc.delete_policy_item(current_user.id, policy_id, item_id)
    return APIResponse(message="保障項目已刪除")

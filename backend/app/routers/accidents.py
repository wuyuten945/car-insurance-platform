from fastapi import APIRouter, Depends, UploadFile, File, Form, Query, Request
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.rate_limit import limiter
from app.dependencies import get_db, get_current_user
from app.exceptions import BadRequestError
from app.models.user import User
from app.models.policy import Policy
from app.schemas.accident import AccidentCreate, AccidentOut, AccidentPhotoOut, NearbyResource
from app.schemas.common import APIResponse
from app.services.accident_service import AccidentService

router = APIRouter()


async def _assert_user_can_upload_accident_photo(db: AsyncSession, user_id: str) -> None:
    """事故照片上傳：要求至少一張 agent 建檔的保單（前後端共同 gate）"""
    res = await db.execute(
        select(func.count()).select_from(Policy).where(
            Policy.user_id == user_id, Policy.data_source == "agent"
        )
    )
    if (res.scalar() or 0) == 0:
        raise BadRequestError(
            "事故照片上傳功能限投保客戶使用。您目前的保單為自行建檔，"
            "理賠 / 事故流程需由業務員 / 平台建立正式保單後才能啟動。"
            "請透過 LINE 官方帳號與我們聯繫。"
        )


@router.post("", response_model=APIResponse)
async def create_accident(
    data: AccidentCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """建立事故記錄"""
    svc = AccidentService(db)
    accident = await svc.create_accident(current_user.id, data)
    return APIResponse(data=AccidentOut.model_validate(accident), message="事故記錄已建立")


@router.get("", response_model=APIResponse)
async def list_accidents(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """取得事故列表"""
    svc = AccidentService(db)
    accidents = await svc.list_accidents(current_user.id)
    return APIResponse(data=[AccidentOut.model_validate(a) for a in accidents])


@router.get("/{accident_id}", response_model=APIResponse)
async def get_accident(
    accident_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """取得事故詳情"""
    svc = AccidentService(db)
    accident = await svc.get_accident(current_user.id, accident_id)
    return APIResponse(data=AccidentOut.model_validate(accident))


@router.post("/{accident_id}/photos", response_model=APIResponse)
@limiter.limit("30/hour")  # 防上傳濫用:單帳號每小時最多 30 張事故照
async def upload_photo(
    request: Request,
    accident_id: str,
    file: UploadFile = File(...),
    photo_type: str = Form(None),
    latitude: float = Form(None),
    longitude: float = Form(None),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """上傳事故照片（限投保客戶 — 即名下需有 agent 建檔保單）"""
    from app.core.upload_validation import validate_upload
    await validate_upload(file, kind="image", max_mb=10)
    await _assert_user_can_upload_accident_photo(db, current_user.id)
    svc = AccidentService(db)
    photo = await svc.upload_photo(accident_id, file, photo_type, latitude, longitude)
    return APIResponse(data=AccidentPhotoOut.model_validate(photo), message="照片已上傳")


@router.get("/{accident_id}/nearby", response_model=APIResponse)
async def get_nearby_resources(
    accident_id: str,
    latitude: float = Query(...),
    longitude: float = Query(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """取得附近資源（警局、拖吊、修車廠）"""
    svc = AccidentService(db)
    resources = await svc.get_nearby_resources(latitude, longitude)
    return APIResponse(data=resources)

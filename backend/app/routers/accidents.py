from fastapi import APIRouter, Depends, UploadFile, File, Form, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.dependencies import get_db, get_current_user
from app.models.user import User
from app.schemas.accident import AccidentCreate, AccidentOut, AccidentPhotoOut, NearbyResource
from app.schemas.common import APIResponse
from app.services.accident_service import AccidentService

router = APIRouter()


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
async def upload_photo(
    accident_id: str,
    file: UploadFile = File(...),
    photo_type: str = Form(None),
    latitude: float = Form(None),
    longitude: float = Form(None),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """上傳事故照片"""
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

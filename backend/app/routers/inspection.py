from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.dependencies import get_db
from app.schemas.inspection import InspectionStationOut
from app.schemas.common import APIResponse
from app.services.inspection_service import InspectionService, _to_out

router = APIRouter()


@router.get("/cities", response_model=APIResponse)
async def list_cities(
    db: AsyncSession = Depends(get_db),
):
    """取得所有縣市列表（不需登入）"""
    svc = InspectionService(db)
    cities = await svc.get_cities()
    return APIResponse(data=cities)


@router.get("/search", response_model=APIResponse)
async def search_stations(
    keyword: str = Query(None, description="關鍵字搜尋（站名、地址、服務）"),
    city: str = Query(None, description="縣市篩選"),
    station_type: str = Query(None, description="類型: supervision=監理站, inspection=驗車廠"),
    latitude: float = Query(None, description="使用者緯度"),
    longitude: float = Query(None, description="使用者經度"),
    radius_km: float = Query(50, description="搜尋半徑（公里）"),
    db: AsyncSession = Depends(get_db),
):
    """搜尋監理站/驗車廠（不需登入，支援關鍵字 + 定位 + 篩選）"""
    svc = InspectionService(db)
    results = await svc.search_stations(
        keyword=keyword,
        city=city,
        station_type=station_type,
        latitude=latitude,
        longitude=longitude,
        radius_km=radius_km,
    )
    return APIResponse(data=results)


@router.get("/nearby", response_model=APIResponse)
async def nearby_stations(
    latitude: float = Query(..., description="使用者緯度"),
    longitude: float = Query(..., description="使用者經度"),
    radius_km: float = Query(30, description="搜尋半徑（公里）"),
    station_type: str = Query(None, description="類型: supervision=監理站, inspection=驗車廠"),
    db: AsyncSession = Depends(get_db),
):
    """以 GPS 座標搜尋附近站點（不需登入）"""
    svc = InspectionService(db)
    results = await svc.nearby_stations(
        latitude=latitude,
        longitude=longitude,
        radius_km=radius_km,
        station_type=station_type,
    )
    return APIResponse(data=results)


@router.get("", response_model=APIResponse)
async def list_inspection_stations(
    city: str = Query(None, description="縣市篩選"),
    station_type: str = Query(None, description="類型: supervision=監理站, inspection=驗車廠"),
    db: AsyncSession = Depends(get_db),
):
    """查詢全部監理站/驗車廠（不需登入）"""
    svc = InspectionService(db)
    stations = await svc.list_stations(city, station_type)
    return APIResponse(data=[_to_out(s) for s in stations])

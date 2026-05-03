from decimal import Decimal
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.dependencies import get_db, get_current_user
from app.models.user import User
from app.schemas.rental import RentalCarOut, RentalCostEstimate
from app.schemas.common import APIResponse
from app.services.rental_service import RentalService

router = APIRouter()


@router.get("", response_model=APIResponse)
async def list_rental_cars(
    latitude: float = Query(...),
    longitude: float = Query(...),
    radius_km: float = Query(5.0),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """查詢附近租車行"""
    svc = RentalService(db)
    cars = await svc.list_nearby(latitude, longitude, radius_km)
    return APIResponse(data=[RentalCarOut.model_validate(c) for c in cars])


@router.get("/estimate", response_model=APIResponse)
async def estimate_cost(
    daily_rate: Decimal = Query(...),
    rental_days: int = Query(..., ge=1),
    insurance_fee: Decimal = Query(Decimal("0")),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """代步車費用試算"""
    svc = RentalService(db)
    estimate = svc.estimate_cost(daily_rate, rental_days, insurance_fee)
    return APIResponse(data=estimate)

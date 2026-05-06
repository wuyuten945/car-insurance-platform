from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.dependencies import get_db, get_current_user
from app.models.user import User
from app.models.vehicle import UserVehicle
from app.schemas.policy import RenewalQuoteOut
from app.schemas.common import APIResponse
from app.services.policy_service import PolicyService
from app.services.renewal_service import RenewalService

router = APIRouter()


class EstimateInput(BaseModel):
    vehicle_id: str | None = None      # 從現有車輛帶入（優先）
    vehicle_type: str | None = None    # 自行輸入時的欄位
    year: int | None = None
    engine_cc: int | None = None
    driver_age: int | None = None
    coverage_tier: str = "standard"    # basic / standard / premium
    include_compulsory: bool = True


@router.post("/estimate", response_model=APIResponse)
async def estimate_quotes(
    payload: EstimateInput,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    續保 / 新保 保費報價（指示性試算）— 不需要既有保單，給前台「續保保費報價」功能用。
    優先從 vehicle_id 抓車輛資料；沒有就用 payload 內手動填入的欄位。
    """
    veh_type, year, cc = payload.vehicle_type, payload.year, payload.engine_cc
    if payload.vehicle_id:
        r = await db.execute(
            select(UserVehicle).where(
                UserVehicle.id == payload.vehicle_id,
                UserVehicle.user_id == current_user.id,
            )
        )
        v = r.scalar_one_or_none()
        if v:
            veh_type = veh_type or v.vehicle_type
            year = year or v.year
            cc = cc or v.engine_cc

    quotes = RenewalService.estimate_from_input(
        vehicle_type=veh_type, year=year, engine_cc=cc,
        driver_age=payload.driver_age,
        coverage_tier=payload.coverage_tier,
        include_compulsory=payload.include_compulsory,
    )
    return APIResponse(
        data={
            "input_used": {
                "vehicle_type": veh_type, "year": year, "engine_cc": cc,
                "driver_age": payload.driver_age,
                "coverage_tier": payload.coverage_tier,
                "include_compulsory": payload.include_compulsory,
            },
            "quotes": quotes,
            "disclaimer": "此為指示性試算，實際保費仍須由保險公司核保確認。如需正式投保請聯繫業務員或透過 LINE 與我們聯繫。",
        },
        message="報價試算完成",
    )


@router.get("/quotes", response_model=APIResponse)
async def get_renewal_quotes(
    policy_id: str = Query(..., description="保單 ID"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """取得續保報價比較"""
    svc = PolicyService(db)
    quotes = await svc.list_renewal_quotes(policy_id)
    if not quotes:
        renewal_svc = RenewalService(db)
        quotes = await renewal_svc.generate_quotes(policy_id)
    return APIResponse(data=[RenewalQuoteOut.model_validate(q) for q in quotes])


@router.post("/quotes/{quote_id}/select", response_model=APIResponse)
async def select_quote(
    quote_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """選擇續保方案"""
    svc = PolicyService(db)
    quote = await svc.select_quote(current_user.id, quote_id)
    return APIResponse(data=RenewalQuoteOut.model_validate(quote), message="已選擇此續保方案")

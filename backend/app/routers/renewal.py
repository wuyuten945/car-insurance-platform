from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.dependencies import get_db, get_current_user
from app.models.user import User
from app.schemas.policy import RenewalQuoteOut
from app.schemas.common import APIResponse
from app.services.policy_service import PolicyService
from app.services.renewal_service import RenewalService

router = APIRouter()


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

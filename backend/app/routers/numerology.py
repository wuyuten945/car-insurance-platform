"""
數字易經代理 router — 把前後端的請求轉發到 numerology-easing.onrender.com 上的既有服務。
原服務有完整的數字易經演算法（八磁場相剋、年齡分區、伏位細分、磁場強化等）。
我們不重做，只做代理 + 共用 BOPINAN 認證。
"""
import logging
import httpx
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from app.dependencies import get_current_user
from app.models.user import User
from app.schemas.common import APIResponse
from app.exceptions import BadRequestError

router = APIRouter()
logger = logging.getLogger(__name__)

NUMEROLOGY_BASE = "https://numerology-easing.onrender.com"
TIMEOUT = httpx.Timeout(60.0, connect=30.0)  # Render free tier 喚醒可能要 30s


class AutoIn(BaseModel):
    id: str | None = None
    phone: str | None = None
    license: str | None = None


class AnalyzeIn(BaseModel):
    input: str
    mode: str = "general"


class RecommendIn(BaseModel):
    purpose: str         # 'phone' | 'license' | 'pin'
    length: int
    prefix: str = ""
    exclude_magnets: list[str] = []
    require_magnets: list[str] = []
    top_n: int = 5       # 前台預設 5；後台 admin 可傳 30


async def _proxy_post(path: str, payload: dict) -> dict:
    url = f"{NUMEROLOGY_BASE}{path}"
    try:
        async with httpx.AsyncClient(timeout=TIMEOUT) as client:
            r = await client.post(url, json=payload)
            r.raise_for_status()
            return r.json()
    except httpx.HTTPStatusError as e:
        logger.warning(f"numerology API {path} returned {e.response.status_code}")
        raise BadRequestError(f"數字易經服務回應 {e.response.status_code}")
    except (httpx.TimeoutException, httpx.NetworkError) as e:
        logger.warning(f"numerology API {path} network: {e}")
        raise BadRequestError("數字易經服務暫時無法連線（可能在啟動中，請稍候 30 秒再試）")
    except Exception as e:
        logger.exception(f"numerology API {path} unexpected: {e}")
        raise BadRequestError("數字易經服務錯誤")


@router.post("/auto", response_model=APIResponse)
async def auto_analyze(
    payload: AutoIn,
    current_user: User = Depends(get_current_user),
):
    """個人分析：身分證 / 電話 / 車牌 一鍵綜合分析"""
    body = {
        "id": payload.id or "",
        "phone": payload.phone or "",
        "license": payload.license or "",
    }
    if not any(body.values()):
        raise BadRequestError("請至少輸入一項")
    result = await _proxy_post("/api/auto", body)
    return APIResponse(data=result)


@router.post("/analyze", response_model=APIResponse)
async def analyze_number(
    payload: AnalyzeIn,
    current_user: User = Depends(get_current_user),
):
    """進階分析：單組或多組合併號碼分析"""
    val = (payload.input or "").strip()
    if not val:
        raise BadRequestError("請輸入號碼")
    result = await _proxy_post("/api/analyze", {"input": val, "mode": payload.mode})
    return APIResponse(data=result)


@router.post("/recommend", response_model=APIResponse)
async def recommend_numbers(
    payload: RecommendIn,
    current_user: User = Depends(get_current_user),
):
    """智能建議：依個人凶星避開 + 補對應吉星，產生 N 組高分號碼"""
    body = payload.model_dump()
    # 後台允許 top_n 高達 30；前台預設 5
    if body["top_n"] < 1:
        body["top_n"] = 5
    if body["top_n"] > 50:
        body["top_n"] = 50
    result = await _proxy_post("/api/recommend", body)
    return APIResponse(data=result)

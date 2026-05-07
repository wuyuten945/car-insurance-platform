"""
數字易經 router — 直接使用內建 engine（從 numerology-easing 移植）。
不再依賴外部 numerology-easing.onrender.com，避免上游 Cloudflare 對
Render server IP 限流（429）的問題。

API 介面與 numerology-easing 完全相容，前端 / admin 不需要改動。
"""
import logging
from concurrent.futures import ThreadPoolExecutor
import asyncio

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.dependencies import get_current_user
from app.exceptions import BadRequestError
from app.models.user import User
from app.schemas.common import APIResponse
from app.services import numerology_engine as engine

router = APIRouter()
logger = logging.getLogger(__name__)

# recommend() 會跑 1000-2000 次 analyze，是 CPU bound，不要阻塞 event loop。
_EXECUTOR = ThreadPoolExecutor(max_workers=2, thread_name_prefix="numerology")


class AutoIn(BaseModel):
    id: str | None = None
    phone: str | None = None
    license: str | None = None


class AnalyzeIn(BaseModel):
    input: str
    mode: str = "general"


class RecommendIn(BaseModel):
    purpose: str = "phone"        # 'phone' | 'license' | 'pin'
    length: int = 10
    prefix: str = ""
    exclude_magnets: list[str] = []
    require_magnets: list[str] = []
    top_n: int = 5                # 前台預設 5；後台 admin 可傳 30


def _safe_analyze(seq: str, mode: str) -> tuple[dict | None, str | None]:
    try:
        return engine.analyze(seq, mode=mode), None
    except (KeyError, ValueError) as e:
        return None, str(e)


def _safe_age_mapping(id_str: str) -> tuple[dict | None, str | None]:
    try:
        return engine.age_mapping(id_str), None
    except (KeyError, ValueError) as e:
        return None, str(e)


@router.post("/auto", response_model=APIResponse)
async def auto_analyze(
    payload: AutoIn,
    current_user: User = Depends(get_current_user),
):
    """個人分析：身分證 / 電話 / 車牌 一鍵綜合分析。"""
    if not (payload.id or payload.phone or payload.license):
        raise BadRequestError("請至少輸入一項")

    out: dict = {}
    if payload.id:
        result, err = _safe_analyze(payload.id, "id")
        if result is not None:
            out["id"] = result
            am, am_err = _safe_age_mapping(payload.id)
            if am is not None:
                out["age_mapping"] = am
            elif am_err:
                out["age_mapping_error"] = am_err
        else:
            out["id_error"] = err

    if payload.phone:
        result, err = _safe_analyze(payload.phone, "general")
        if result is not None:
            out["phone"] = result
        else:
            out["phone_error"] = err

    if payload.license:
        result, err = _safe_analyze(payload.license, "general")
        if result is not None:
            out["license"] = result
        else:
            out["license_error"] = err

    return APIResponse(data=out)


@router.post("/analyze", response_model=APIResponse)
async def analyze_number(
    payload: AnalyzeIn,
    current_user: User = Depends(get_current_user),
):
    """進階分析：單組或多組合併號碼分析。"""
    val = (payload.input or "").strip()
    if not val:
        raise BadRequestError("請輸入號碼")
    result, err = _safe_analyze(val, payload.mode or "general")
    if result is None:
        raise BadRequestError(err or "分析失敗")
    return APIResponse(data=result)


@router.post("/recommend", response_model=APIResponse)
async def recommend_numbers(
    payload: RecommendIn,
    current_user: User = Depends(get_current_user),
):
    """智能建議：依個人凶星避開 + 補對應吉星，產生 N 組高分號碼。"""
    top_n = max(1, min(payload.top_n, 50))
    constraints = {
        "purpose": payload.purpose,
        "length": int(payload.length),
        "prefix": payload.prefix,
        "exclude_magnets": payload.exclude_magnets,
        "require_magnets": payload.require_magnets,
        "candidate_pool": 2000,
    }
    loop = asyncio.get_running_loop()
    try:
        recs = await loop.run_in_executor(
            _EXECUTOR, lambda: engine.recommend(constraints, top_n=top_n)
        )
    except (KeyError, ValueError) as e:
        raise BadRequestError(str(e))
    except Exception as e:
        logger.exception(f"numerology recommend failed: {e}")
        raise BadRequestError("智能建議產生失敗,請調整條件後重試")
    return APIResponse(data={"recommendations": recs, "constraints": constraints})

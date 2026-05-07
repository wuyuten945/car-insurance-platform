"""
數字易經代理 router — 把前後端的請求轉發到 numerology-easing.onrender.com 上的既有服務。
原服務有完整的數字易經演算法（八磁場相剋、年齡分區、伏位細分、磁場強化等）。
我們不重做，只做代理 + 共用 BOPINAN 認證。
"""
import asyncio
import hashlib
import json
import logging
import time
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

# 簡單的記憶體快取（同一輸入 5 分鐘內回傳同樣結果，省上游 API 配額）
_CACHE: dict[str, tuple[float, dict]] = {}
_CACHE_TTL = 300.0  # 5 min
_CACHE_MAX = 500


def _cache_key(path: str, payload: dict) -> str:
    raw = path + "|" + json.dumps(payload, sort_keys=True, ensure_ascii=False)
    return hashlib.sha1(raw.encode("utf-8")).hexdigest()


def _cache_get(key: str) -> dict | None:
    entry = _CACHE.get(key)
    if not entry:
        return None
    ts, val = entry
    if time.time() - ts > _CACHE_TTL:
        _CACHE.pop(key, None)
        return None
    return val


def _cache_set(key: str, val: dict) -> None:
    if len(_CACHE) >= _CACHE_MAX:
        # 清掉最舊 1/4
        for k, _ in sorted(_CACHE.items(), key=lambda kv: kv[1][0])[: _CACHE_MAX // 4]:
            _CACHE.pop(k, None)
    _CACHE[key] = (time.time(), val)


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


async def _proxy_post(path: str, payload: dict, *, use_cache: bool = True) -> dict:
    url = f"{NUMEROLOGY_BASE}{path}"
    cache_key = _cache_key(path, payload) if use_cache else ""

    # 1) 快取命中
    if use_cache:
        cached = _cache_get(cache_key)
        if cached is not None:
            return cached

    # 2) 呼叫上游（429 / 5xx 可重試最多 2 次，指數退讓）
    last_err: Exception | None = None
    for attempt in range(3):
        try:
            async with httpx.AsyncClient(timeout=TIMEOUT) as client:
                r = await client.post(url, json=payload)
            if r.status_code == 429:
                last_err = httpx.HTTPStatusError("429", request=r.request, response=r)
                if attempt < 2:
                    await asyncio.sleep(1.5 * (2 ** attempt))  # 1.5s, 3s
                    continue
                logger.warning(f"numerology API {path} 429 after {attempt+1} attempts")
                raise BadRequestError("查詢頻率過高,請等 30 秒後再試一次")
            if 500 <= r.status_code < 600:
                last_err = httpx.HTTPStatusError(str(r.status_code), request=r.request, response=r)
                if attempt < 2:
                    await asyncio.sleep(1.0 * (2 ** attempt))
                    continue
            r.raise_for_status()
            data = r.json()
            if use_cache:
                _cache_set(cache_key, data)
            return data
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 429:
                # 已在上面處理
                raise BadRequestError("查詢頻率過高,請等 30 秒後再試一次")
            logger.warning(f"numerology API {path} returned {e.response.status_code}")
            raise BadRequestError(f"數字易經服務回應 {e.response.status_code}")
        except (httpx.TimeoutException, httpx.NetworkError) as e:
            last_err = e
            if attempt < 2:
                await asyncio.sleep(1.0 * (2 ** attempt))
                continue
            logger.warning(f"numerology API {path} network: {e}")
            raise BadRequestError("數字易經服務暫時無法連線（可能在啟動中,請稍候 30 秒再試）")
        except BadRequestError:
            raise
        except Exception as e:
            logger.exception(f"numerology API {path} unexpected: {e}")
            raise BadRequestError("數字易經服務錯誤")

    # 理論上不會到這裡
    logger.warning(f"numerology API {path} exhausted retries: {last_err}")
    raise BadRequestError("數字易經服務暫時無法回應,請稍候再試")


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

"""
數字易經 router — 直接使用內建 engine（從 numerology-easing 移植）。
不再依賴外部 numerology-easing.onrender.com，避免上游 Cloudflare 對
Render server IP 限流（429）的問題。

API 介面與 numerology-easing 完全相容，前端 / admin 不需要改動。
"""
import logging
from concurrent.futures import ThreadPoolExecutor
import asyncio

from fastapi import APIRouter, Depends, Header
from pydantic import BaseModel

from app.core.security import decode_token
from app.exceptions import BadRequestError, UnauthorizedError
from app.schemas.common import APIResponse
from app.services import numerology_engine as engine

router = APIRouter()
logger = logging.getLogger(__name__)

# recommend() 會跑 1000-2000 次 analyze，是 CPU bound，不要阻塞 event loop。
_EXECUTOR = ThreadPoolExecutor(max_workers=2, thread_name_prefix="numerology")


# ─────────────────────────────────────────────────────────────
# 統一認證：接受客戶 token (type=access) 或管理員 token (type=admin)
# ─────────────────────────────────────────────────────────────
async def require_any_auth(
    authorization: str = Header(..., description="Bearer <token>"),
) -> dict:
    """數字易經是後台 admin / agent 與前台客戶都會使用的功能,故兩種 JWT 都允許。
    僅驗證 token 有效,不抓使用者物件(numerology endpoint 本身不需要)。
    """
    if not authorization.startswith("Bearer "):
        raise UnauthorizedError("無效的授權標頭")
    token = authorization[7:]
    payload = decode_token(token)
    if not payload:
        raise UnauthorizedError("無效或過期的 Token")
    token_type = payload.get("type")
    if token_type not in ("access", "admin"):
        raise UnauthorizedError("無效或過期的 Token")
    return payload


class AutoIn(BaseModel):
    id: str | None = None
    birthday: str | None = None     # 西元生日 YYYY/MM/DD（slash 等非數字字元 engine 會自動 strip）
    phone: str | None = None
    phone2: str | None = None       # 第二支電話（選填）
    license: str | None = None
    license2: str | None = None     # 第二台車牌（選填）


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
    _auth: dict = Depends(require_any_auth),
):
    """個人分析：身分證 / 生日 / 電話 ×2 / 車牌 ×2 一鍵綜合分析。"""
    fields = [payload.id, payload.birthday, payload.phone, payload.phone2,
              payload.license, payload.license2]
    if not any(f for f in fields):
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

    if payload.birthday:
        # engine.letter_to_digits 會自動 strip /、-、空白等非英數字元
        result, err = _safe_analyze(payload.birthday, "general")
        if result is not None:
            out["birthday"] = result
        else:
            out["birthday_error"] = err

    if payload.phone:
        result, err = _safe_analyze(payload.phone, "general")
        if result is not None:
            out["phone"] = result
        else:
            out["phone_error"] = err

    if payload.phone2:
        result, err = _safe_analyze(payload.phone2, "general")
        if result is not None:
            out["phone2"] = result
        else:
            out["phone2_error"] = err

    if payload.license:
        result, err = _safe_analyze(payload.license, "general")
        if result is not None:
            out["license"] = result
        else:
            out["license_error"] = err

    if payload.license2:
        result, err = _safe_analyze(payload.license2, "general")
        if result is not None:
            out["license2"] = result
        else:
            out["license2_error"] = err

    return APIResponse(data=out)


@router.post("/analyze", response_model=APIResponse)
async def analyze_number(
    payload: AnalyzeIn,
    _auth: dict = Depends(require_any_auth),
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
    _auth: dict = Depends(require_any_auth),
):
    """智能建議:依個人凶星避開 + 補對應吉星,產生 N 組高分號碼。

    Server-side 規則:**強制排除所有 4 個凶星**(絕命/五鬼/六煞/禍害),
    無論前端傳什麼,生成的號碼一律不含任何凶星磁場。
    """
    top_n = max(1, min(payload.top_n, 50))
    # 強制把 4 個凶星全部加進 exclude(用 set 去重後仍以 list 傳遞)
    _user_exclude = payload.exclude_magnets or []
    _forced_exclude = list({*_user_exclude, *engine.BAD_MAGNETS})
    constraints = {
        "purpose": payload.purpose,
        "length": int(payload.length),
        "prefix": payload.prefix,
        "exclude_magnets": _forced_exclude,
        "require_magnets": payload.require_magnets,
        # 排除全 4 個凶星後候選池要更大(~512 倍稀疏度),從 2000 拉到 8000
        "candidate_pool": 8000,
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
    if not recs:
        # 完全找不到無凶星號碼(極稀有 — 通常 prefix 限制太嚴格)
        raise BadRequestError(
            "在此 prefix / 長度條件下找不到完全無凶星的號碼,請放寬 prefix 或調整長度後再試。"
        )
    return APIResponse(data={"recommendations": recs, "constraints": constraints})

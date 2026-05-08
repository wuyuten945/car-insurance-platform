"""
全域 rate limiter 實例 — 單一定義點,讓 router 可加 @limiter.limit() 裝飾器。
"""
from fastapi import Request
from slowapi import Limiter
from slowapi.util import get_remote_address


def _real_client_ip(request: Request) -> str:
    """Render/Cloudflare 等代理後的真實 client IP。"""
    fwd = request.headers.get("x-forwarded-for")
    if fwd:
        first = fwd.split(",")[0].strip()
        if first:
            return first
    real = request.headers.get("x-real-ip")
    if real:
        return real.strip()
    return get_remote_address(request)


def _rate_limit_key(request: Request) -> str:
    """以 Bearer token (前 16 字) 為主 key,沒 token 退化用 IP。"""
    auth = request.headers.get("authorization") or ""
    if auth.startswith("Bearer "):
        token = auth[7:]
        return f"tok:{token[:16]}"
    return f"ip:{_real_client_ip(request)}"


limiter = Limiter(
    key_func=_rate_limit_key,
    default_limits=["120/minute", "2000/hour"],
    headers_enabled=True,
)

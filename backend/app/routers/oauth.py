"""
OAuth 社交登入 — Google / Apple / Facebook
"""
import logging
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, Query
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_

from app.dependencies import get_db
from app.models.user import User
from app.schemas.common import APIResponse
from app.core.security import create_access_token, create_refresh_token
from app.config import settings

logger = logging.getLogger(__name__)
router = APIRouter()


async def _oauth_login(db: AsyncSession, email: str, name: str = "", provider: str = "") -> dict:
    """共用：用 email 查找/建立用戶，回傳 tokens"""
    result = await db.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()

    if not user:
        user = User(email=email, name=name or email.split("@")[0])
        db.add(user)
        await db.flush()
        logger.info(f"OAuth 新用戶: {email} via {provider}")
    else:
        if name and not user.name:
            user.name = name

    user.last_login_at = datetime.now(timezone.utc)

    access_token = create_access_token(user.id)
    refresh_token = create_refresh_token(user.id)

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "user_id": user.id,
        "user_name": user.name or "",
        "user_email": user.email or "",
    }


# ════════════════════════════════════════════════════════════════
# Google OAuth
# ════════════════════════════════════════════════════════════════

@router.get("/google/login")
async def google_login():
    """重導到 Google OAuth 授權頁"""
    if not settings.GOOGLE_CLIENT_ID:
        return APIResponse(success=False, message="Google OAuth 未設定")
    redirect_uri = f"{settings.BACKEND_URL}/api/v1/oauth/google/callback"
    url = (
        "https://accounts.google.com/o/oauth2/v2/auth?"
        f"client_id={settings.GOOGLE_CLIENT_ID}"
        f"&redirect_uri={redirect_uri}"
        "&response_type=code"
        "&scope=openid%20email%20profile"
        "&access_type=offline"
    )
    return RedirectResponse(url)


@router.get("/google/callback")
async def google_callback(code: str = Query(...), db: AsyncSession = Depends(get_db)):
    """Google OAuth 回呼"""
    import httpx
    redirect_uri = f"{settings.BACKEND_URL}/api/v1/oauth/google/callback"

    # Exchange code for token
    async with httpx.AsyncClient() as client:
        token_resp = await client.post("https://oauth2.googleapis.com/token", data={
            "code": code,
            "client_id": settings.GOOGLE_CLIENT_ID,
            "client_secret": settings.GOOGLE_CLIENT_SECRET,
            "redirect_uri": redirect_uri,
            "grant_type": "authorization_code",
        })
        tokens = token_resp.json()

        # Get user info
        userinfo_resp = await client.get("https://www.googleapis.com/oauth2/v2/userinfo",
                                          headers={"Authorization": f"Bearer {tokens['access_token']}"})
        userinfo = userinfo_resp.json()

    email = userinfo.get("email", "")
    name = userinfo.get("name", "")
    if not email:
        return RedirectResponse(f"{settings.OAUTH_REDIRECT_BASE}/login?error=no_email")

    result = await _oauth_login(db, email, name, "google")
    # Redirect to frontend with tokens
    return RedirectResponse(
        f"{settings.OAUTH_REDIRECT_BASE}/auth/callback/success"
        f"?access_token={result['access_token']}"
        f"&refresh_token={result['refresh_token']}"
        f"&name={result['user_name']}"
    )


# ════════════════════════════════════════════════════════════════
# Apple OAuth
# ════════════════════════════════════════════════════════════════

@router.get("/apple/login")
async def apple_login():
    """重導到 Apple OAuth 授權頁"""
    if not settings.APPLE_CLIENT_ID:
        return APIResponse(success=False, message="Apple OAuth 未設定")
    redirect_uri = f"{settings.OAUTH_REDIRECT_BASE}/auth/callback/apple"
    url = (
        "https://appleid.apple.com/auth/authorize?"
        f"client_id={settings.APPLE_CLIENT_ID}"
        f"&redirect_uri={redirect_uri}"
        "&response_type=code"
        "&scope=name%20email"
        "&response_mode=form_post"
    )
    return RedirectResponse(url)


@router.post("/apple/callback")
async def apple_callback(code: str = Query(""), db: AsyncSession = Depends(get_db)):
    """Apple OAuth 回呼"""
    import httpx, jwt as pyjwt
    redirect_uri = f"{settings.OAUTH_REDIRECT_BASE}/auth/callback/apple"

    # Generate client_secret JWT
    import time
    now = int(time.time())
    headers = {"kid": settings.APPLE_KEY_ID, "alg": "ES256"}
    payload = {
        "iss": settings.APPLE_TEAM_ID,
        "iat": now,
        "exp": now + 86400 * 180,
        "aud": "https://appleid.apple.com",
        "sub": settings.APPLE_CLIENT_ID,
    }
    client_secret = pyjwt.encode(payload, settings.APPLE_PRIVATE_KEY, algorithm="ES256", headers=headers)

    async with httpx.AsyncClient() as client:
        token_resp = await client.post("https://appleid.apple.com/auth/token", data={
            "code": code,
            "client_id": settings.APPLE_CLIENT_ID,
            "client_secret": client_secret,
            "redirect_uri": redirect_uri,
            "grant_type": "authorization_code",
        })
        tokens = token_resp.json()

    id_token = tokens.get("id_token", "")
    if id_token:
        decoded = pyjwt.decode(id_token, options={"verify_signature": False})
        email = decoded.get("email", "")
    else:
        return RedirectResponse(f"{settings.OAUTH_REDIRECT_BASE}/login?error=apple_failed")

    result = await _oauth_login(db, email, "", "apple")
    return RedirectResponse(
        f"{settings.OAUTH_REDIRECT_BASE}/auth/callback/success"
        f"?access_token={result['access_token']}"
        f"&refresh_token={result['refresh_token']}"
    )


# ════════════════════════════════════════════════════════════════
# Facebook OAuth
# ════════════════════════════════════════════════════════════════

@router.get("/facebook/login")
async def facebook_login():
    """重導到 Facebook OAuth 授權頁"""
    if not settings.FACEBOOK_CLIENT_ID:
        return APIResponse(success=False, message="Facebook OAuth 未設定")
    redirect_uri = f"{settings.OAUTH_REDIRECT_BASE}/auth/callback/facebook"
    url = (
        "https://www.facebook.com/v18.0/dialog/oauth?"
        f"client_id={settings.FACEBOOK_CLIENT_ID}"
        f"&redirect_uri={redirect_uri}"
        "&scope=email,public_profile"
    )
    return RedirectResponse(url)


@router.get("/facebook/callback")
async def facebook_callback(code: str = Query(...), db: AsyncSession = Depends(get_db)):
    """Facebook OAuth 回呼"""
    import httpx
    redirect_uri = f"{settings.OAUTH_REDIRECT_BASE}/auth/callback/facebook"

    async with httpx.AsyncClient() as client:
        # Exchange code for token
        token_resp = await client.get("https://graph.facebook.com/v18.0/oauth/access_token", params={
            "code": code,
            "client_id": settings.FACEBOOK_CLIENT_ID,
            "client_secret": settings.FACEBOOK_CLIENT_SECRET,
            "redirect_uri": redirect_uri,
        })
        tokens = token_resp.json()

        # Get user info
        me_resp = await client.get("https://graph.facebook.com/me", params={
            "access_token": tokens["access_token"],
            "fields": "id,name,email",
        })
        me = me_resp.json()

    email = me.get("email", "")
    name = me.get("name", "")
    if not email:
        return RedirectResponse(f"{settings.OAUTH_REDIRECT_BASE}/login?error=no_email")

    result = await _oauth_login(db, email, name, "facebook")
    return RedirectResponse(
        f"{settings.OAUTH_REDIRECT_BASE}/auth/callback/success"
        f"?access_token={result['access_token']}"
        f"&refresh_token={result['refresh_token']}"
        f"&name={result['user_name']}"
    )


# ════════════════════════════════════════════════════════════════
# 可用的 OAuth 提供者查詢
# ════════════════════════════════════════════════════════════════

@router.get("/providers")
async def list_providers():
    """回傳已設定的 OAuth 提供者"""
    providers = []
    if settings.GOOGLE_CLIENT_ID:
        providers.append({"name": "google", "label": "Google", "url": "/api/v1/oauth/google/login"})
    if settings.APPLE_CLIENT_ID:
        providers.append({"name": "apple", "label": "Apple", "url": "/api/v1/oauth/apple/login"})
    if settings.FACEBOOK_CLIENT_ID:
        providers.append({"name": "facebook", "label": "Facebook", "url": "/api/v1/oauth/facebook/login"})
    return APIResponse(data=providers)

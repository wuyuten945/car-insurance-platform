from fastapi import APIRouter, Depends, Header, Request
from sqlalchemy.ext.asyncio import AsyncSession
from app.dependencies import get_db
from app.schemas.auth import OTPSendRequest, OTPVerifyRequest, TokenResponse, RefreshTokenRequest
from app.schemas.user import UserOut
from app.schemas.common import APIResponse
from app.services.auth_service import AuthService
from app.config import settings
from app.core.cache import cache

router = APIRouter()


@router.post("/otp/send", response_model=APIResponse)
async def send_otp(req: OTPSendRequest, request: Request, db: AsyncSession = Depends(get_db)):
    """發送 Email OTP（手機 OTP 已停用以避免 SMS 簡訊費用被惡意刷取）"""
    svc = AuthService(db)
    ip = request.client.host if request.client else ""
    result = await svc.send_otp(email=req.email, ip=ip)
    # 開發模式：回傳 OTP 方便測試
    if settings.DEBUG:
        otp = await cache.get(f"otp:{req.email}")
        result["otp"] = otp
    return APIResponse(data=result, message="驗證碼已發送")


@router.post("/otp/verify", response_model=APIResponse)
async def verify_otp(req: OTPVerifyRequest, db: AsyncSession = Depends(get_db)):
    """驗證 Email OTP 並登入"""
    svc = AuthService(db)
    result = await svc.verify_otp_and_login(email=req.email, otp=req.otp)
    return APIResponse(
        data={
            "user": UserOut.model_validate(result["user"]),
            "tokens": TokenResponse(
                access_token=result["access_token"],
                refresh_token=result["refresh_token"],
                expires_in=result["expires_in"],
            ),
        },
        message="登入成功",
    )


@router.post("/refresh", response_model=APIResponse)
async def refresh_token(req: RefreshTokenRequest, db: AsyncSession = Depends(get_db)):
    """刷新 Token"""
    svc = AuthService(db)
    result = await svc.refresh_tokens(req.refresh_token)
    return APIResponse(
        data=TokenResponse(
            access_token=result["access_token"],
            refresh_token=result["refresh_token"],
            expires_in=result["expires_in"],
        ),
        message="Token 已刷新",
    )


@router.post("/logout", response_model=APIResponse)
async def logout(authorization: str = Header(...), db: AsyncSession = Depends(get_db)):
    """登出"""
    token = authorization.replace("Bearer ", "")
    svc = AuthService(db)
    await svc.logout(token)
    return APIResponse(message="已登出")

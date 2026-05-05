from fastapi import APIRouter, Depends, Header, Request
from sqlalchemy.ext.asyncio import AsyncSession
from app.dependencies import get_db, get_current_user
from app.schemas.auth import (
    OTPSendRequest, OTPVerifyRequest, TokenResponse, RefreshTokenRequest,
    VerifyPasswordRequest, SetPasswordRequest, RemovePasswordRequest,
)
from app.schemas.user import UserOut
from app.schemas.common import APIResponse
from app.services.auth_service import AuthService
from app.models.user import User
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
    """
    驗證 Email OTP。回傳兩種 step：
      - logged_in：未啟用進階保護密碼，直接拿到 access/refresh tokens
      - password_required：已啟用，回傳 interim_token，需呼叫 /verify-password 完成登入
    """
    svc = AuthService(db)
    result = await svc.verify_otp_and_login(email=req.email, otp=req.otp)

    if result.get("step") == "password_required":
        return APIResponse(
            data={
                "step": "password_required",
                "interim_token": result["interim_token"],
                "expires_in": result["expires_in"],
            },
            message="OTP 通過，請輸入進階保護密碼",
        )

    return APIResponse(
        data={
            "step": "logged_in",
            "user": UserOut.model_validate(result["user"]),
            "tokens": TokenResponse(
                access_token=result["access_token"],
                refresh_token=result["refresh_token"],
                expires_in=result["expires_in"],
            ),
        },
        message="登入成功",
    )


@router.post("/verify-password", response_model=APIResponse)
async def verify_password(req: VerifyPasswordRequest, db: AsyncSession = Depends(get_db)):
    """OTP 通過後的二因子驗證：interim_token + password → 正式 tokens"""
    svc = AuthService(db)
    result = await svc.verify_password_with_interim(req.interim_token, req.password)
    return APIResponse(
        data={
            "step": "logged_in",
            "user": UserOut.model_validate(result["user"]),
            "tokens": TokenResponse(
                access_token=result["access_token"],
                refresh_token=result["refresh_token"],
                expires_in=result["expires_in"],
            ),
        },
        message="登入成功",
    )


@router.post("/password/set", response_model=APIResponse)
async def set_advanced_password(
    req: SetPasswordRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """設定或變更進階保護密碼（已登入才可呼叫；改密碼需提供當前密碼）"""
    svc = AuthService(db)
    await svc.set_advanced_password(current_user.id, req.new_password, req.current_password)
    return APIResponse(message="進階保護密碼已設定，下次登入需要驗證")


@router.post("/password/remove", response_model=APIResponse)
async def remove_advanced_password(
    req: RemovePasswordRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """移除進階保護密碼（須提供當前密碼）"""
    svc = AuthService(db)
    await svc.remove_advanced_password(current_user.id, req.current_password)
    return APIResponse(message="進階保護密碼已移除")


@router.get("/password/status", response_model=APIResponse)
async def password_status(current_user: User = Depends(get_current_user)):
    """查詢當前帳號是否啟用進階保護密碼"""
    return APIResponse(data={"enabled": bool(current_user.password_hash)})


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

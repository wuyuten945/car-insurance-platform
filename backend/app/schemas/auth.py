from pydantic import BaseModel, field_validator
import re

from app.core.i18n import t

EMAIL_RE = re.compile(r"^[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}$")


def _validate_email(v: str) -> str:
    v = (v or "").strip().lower()
    if not EMAIL_RE.match(v):
        raise ValueError(t("email_format"))
    return v


# 手機 OTP 已停用（避免 SMS 簡訊被惡意大量觸發產生費用）。
# 客戶登入請使用 Email OTP 或 OAuth（Google / Apple / Facebook）。
class OTPSendRequest(BaseModel):
    email: str
    method: str = "email"

    @field_validator("email")
    @classmethod
    def validate_email(cls, v: str) -> str:
        return _validate_email(v)

    @field_validator("method")
    @classmethod
    def validate_method(cls, v: str) -> str:
        if v != "email":
            raise ValueError(t("method_email_only"))
        return v


class OTPVerifyRequest(BaseModel):
    email: str
    otp: str

    @field_validator("email")
    @classmethod
    def validate_email(cls, v: str) -> str:
        return _validate_email(v)

    @field_validator("otp")
    @classmethod
    def validate_otp(cls, v: str) -> str:
        if not re.match(r"^\d{6}$", v):
            raise ValueError(t("otp_format"))
        return v


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int  # seconds


class RefreshTokenRequest(BaseModel):
    refresh_token: str


class LogoutRequest(BaseModel):
    pass


class VerifyPasswordRequest(BaseModel):
    """OTP 通過後的二因子密碼驗證"""
    interim_token: str
    password: str


class SetPasswordRequest(BaseModel):
    """設定/變更進階保護密碼。第一次設不需 current_password；之後變更需要"""
    new_password: str
    current_password: str | None = None

    @field_validator("new_password")
    @classmethod
    def _new_pw(cls, v: str) -> str:
        if not v or len(v) < 8:
            raise ValueError(t("pw_too_short"))
        return v


class RemovePasswordRequest(BaseModel):
    """移除進階保護密碼（需驗證當前密碼）"""
    current_password: str

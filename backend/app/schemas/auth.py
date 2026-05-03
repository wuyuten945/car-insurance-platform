from pydantic import BaseModel, field_validator
import re

EMAIL_RE = re.compile(r"^[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}$")


def _validate_email(v: str) -> str:
    v = (v or "").strip().lower()
    if not EMAIL_RE.match(v):
        raise ValueError("請輸入有效的 Email 格式")
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
            raise ValueError("僅支援 email 驗證；手機 OTP 已停用")
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
            raise ValueError("驗證碼必須為 6 位數字")
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

"""
Backend i18n 模組

機制：
  1. middleware 從 Accept-Language header 偵測語言（zh / en）
  2. ContextVar 存當前 request 的語言（thread/coroutine-safe）
  3. t(key, **vars) 由 service / router 呼叫產出對應語言訊息

使用：
  from app.core.i18n import t
  raise BadRequestError(t("current_pw_wrong"))
"""
from __future__ import annotations

from contextvars import ContextVar
from fastapi import FastAPI, Request

_lang_ctx: ContextVar[str] = ContextVar("lang", default="zh")


def get_current_lang() -> str:
    return _lang_ctx.get()


def setup_i18n_middleware(app: FastAPI) -> None:
    """掛 middleware：每個 request 從 Accept-Language 抓 zh / en"""

    @app.middleware("http")
    async def _detect_lang(request: Request, call_next):
        accept = (request.headers.get("Accept-Language") or "").lower().strip()
        # 簡單判斷：開頭是 en 才當英文，其他預設中文
        lang = "en" if accept.startswith("en") else "zh"
        token = _lang_ctx.set(lang)
        try:
            response = await call_next(request)
        finally:
            _lang_ctx.reset(token)
        return response


# ── 訊息字典 ─────────────────────────────────────────
MESSAGES: dict[str, dict[str, str]] = {
    "zh": {
        # ── auth / OTP ──
        "email_required": "請提供 Email",
        "email_format": "請輸入有效的 Email 格式",
        "method_email_only": "僅支援 email 驗證；手機 OTP 已停用",
        "otp_format": "驗證碼必須為 6 位數字",
        "otp_rate_email": "OTP 發送過於頻繁，請稍後再試",
        "otp_rate_ip": "此 IP 發送驗證碼過於頻繁，請稍後再試",
        "otp_invalid": "驗證碼錯誤或已過期",
        "otp_sent": "驗證碼已發送",
        "login_success": "登入成功",
        "logout_success": "已登出",
        "token_refreshed": "Token 已刷新",
        "refresh_invalid": "無效的 Refresh Token",
        "user_not_active": "使用者不存在或已停用",
        "auth_invalid_header": "無效的授權標頭",
        "token_revoked": "Token 已失效",
        "token_invalid": "無效或過期的 Token",

        # ── 進階保護密碼 ──
        "pw_otp_step_done": "OTP 通過，請輸入進階保護密碼",
        "pw_session_expired": "驗證階段已過期，請重新登入",
        "pw_not_enabled": "此帳號未啟用進階保護密碼",
        "pw_wrong": "密碼錯誤",
        "pw_current_wrong": "當前密碼錯誤",
        "pw_too_short": "新密碼至少 8 字元",
        "pw_same_as_current": "新密碼不可與當前密碼相同",
        "pw_set_success": "進階保護密碼已設定，下次登入需要驗證",
        "pw_remove_success": "進階保護密碼已移除",
        "pw_change_success": "密碼已變更，下次登入請使用新密碼",
        "pw_invalid_role": "無效的 role：{role}",
        "user_not_found": "使用者不存在",

        # ── admin auth ──
        "admin_invalid_credentials": "帳號或密碼錯誤",
        "admin_disabled": "帳號已停用",
        "admin_ip_not_allowed": "IP {ip} 不在允許清單中",
        "admin_username_exists": "帳號 {username} 已存在",
        "admin_not_found": "業務員不存在",
        "admin_super_required": "需要超級管理員權限",
    },
    "en": {
        "email_required": "Please provide an email",
        "email_format": "Invalid email format",
        "method_email_only": "Only email verification is supported (SMS OTP disabled)",
        "otp_format": "OTP must be 6 digits",
        "otp_rate_email": "Too many OTP requests, please try again later",
        "otp_rate_ip": "Too many requests from this IP, please try again later",
        "otp_invalid": "Invalid or expired verification code",
        "otp_sent": "Verification code sent",
        "login_success": "Login successful",
        "logout_success": "Logged out",
        "token_refreshed": "Token refreshed",
        "refresh_invalid": "Invalid refresh token",
        "user_not_active": "User does not exist or is disabled",
        "auth_invalid_header": "Invalid authorization header",
        "token_revoked": "Token has been revoked",
        "token_invalid": "Invalid or expired token",

        "pw_otp_step_done": "OTP verified — please enter your protection password",
        "pw_session_expired": "Verification session expired, please log in again",
        "pw_not_enabled": "This account does not have advanced protection enabled",
        "pw_wrong": "Wrong password",
        "pw_current_wrong": "Current password is incorrect",
        "pw_too_short": "New password must be at least 8 characters",
        "pw_same_as_current": "New password must differ from current password",
        "pw_set_success": "Advanced protection password set. Next login will require verification.",
        "pw_remove_success": "Advanced protection password removed",
        "pw_change_success": "Password changed. Please use the new password next time you log in.",
        "pw_invalid_role": "Invalid role: {role}",
        "user_not_found": "User not found",

        "admin_invalid_credentials": "Invalid username or password",
        "admin_disabled": "Account disabled",
        "admin_ip_not_allowed": "IP {ip} is not in the allow list",
        "admin_username_exists": "Username {username} already exists",
        "admin_not_found": "Agent not found",
        "admin_super_required": "Super admin privilege required",
    },
}


def t(key: str, **vars) -> str:
    """取當前 request 語言的訊息；未命中 key 則回 zh fallback，再不行回 key 本身"""
    lang = _lang_ctx.get()
    bundle = MESSAGES.get(lang) or MESSAGES["zh"]
    msg = bundle.get(key) or MESSAGES["zh"].get(key) or key
    if vars:
        try:
            return msg.format(**vars)
        except (KeyError, IndexError):
            return msg
    return msg

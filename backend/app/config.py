from pydantic_settings import BaseSettings
from typing import List
import json
import logging
import os
import secrets

logger = logging.getLogger(__name__)

# 安全:JWT 密鑰必須由環境變數提供。若 dev 環境沒設,生成一次性隨機 secret
# (重啟會換,所有 token 失效 — 這是設計上的提醒,要設環境變數)
_DEV_SECRET_FALLBACK = None


def _resolve_jwt_secret() -> str:
    """
    優先順序:
      1. JWT_SECRET_KEY env (production 必須設)
      2. dev 環境(DEBUG=true 且無 RENDER 標記) 自動生成隨機 secret + log warn
      3. production-ish (非 dev) 沒設 → 直接 raise,絕不啟動
    """
    global _DEV_SECRET_FALLBACK
    val = os.environ.get("JWT_SECRET_KEY") or ""
    if val and val not in ("dev-secret-key-change-in-production", "change-this-to-a-random-secret-key"):
        return val
    # 沒設或還在用範例值
    is_render = bool(os.environ.get("RENDER") or os.environ.get("RENDER_SERVICE_ID"))
    debug_env = (os.environ.get("DEBUG") or "").lower() in ("1", "true", "yes")
    if is_render or not debug_env:
        # production / Render 部署環境 → 拒絕啟動
        raise RuntimeError(
            "JWT_SECRET_KEY environment variable is required and must not be the placeholder. "
            "Set it to a strong random value (>= 32 chars) in your deployment environment."
        )
    # dev 環境 → 一次性 secret 並警告
    if _DEV_SECRET_FALLBACK is None:
        _DEV_SECRET_FALLBACK = secrets.token_urlsafe(32)
        logger.warning(
            "[security] JWT_SECRET_KEY not set; generated a temporary dev secret. "
            "Tokens will become invalid on every server restart. "
            "Set JWT_SECRET_KEY in your .env or environment to fix."
        )
    return _DEV_SECRET_FALLBACK


class Settings(BaseSettings):
    # Database
    DATABASE_URL: str = "sqlite+aiosqlite:///./car_insurance.db"

    # JWT — 透過 _resolve_jwt_secret() 強制要求環境變數,沒設或用範例值都不能啟動
    JWT_SECRET_KEY: str = ""
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60   # 從 480 (8hr) 縮為 60 分鐘,降低 token 外洩影響
    REFRESH_TOKEN_EXPIRE_DAYS: int = 30

    # OTP
    OTP_EXPIRE_SECONDS: int = 300
    OTP_LENGTH: int = 6

    # CORS — 用字串避免 pydantic-settings 嘗試 JSON 解析失敗
    # 支援格式：JSON array `["url1","url2"]` 或逗號分隔 `url1,url2`
    CORS_ORIGINS: str = "http://localhost:3000,http://127.0.0.1:3000"

    @property
    def cors_origins_list(self) -> List[str]:
        v = (self.CORS_ORIGINS or "").strip()
        if not v:
            return []
        if v.startswith("["):
            try:
                return json.loads(v)
            except Exception:
                pass
        return [s.strip() for s in v.split(",") if s.strip()]

    # Storage
    UPLOAD_DIR: str = "./uploads"
    MAX_UPLOAD_SIZE_MB: int = 10

    # OAuth Social Login
    GOOGLE_CLIENT_ID: str = ""
    GOOGLE_CLIENT_SECRET: str = ""
    APPLE_CLIENT_ID: str = ""        # Service ID (e.g., com.example.app)
    APPLE_TEAM_ID: str = ""
    APPLE_KEY_ID: str = ""
    APPLE_PRIVATE_KEY: str = ""      # .p8 file content
    FACEBOOK_CLIENT_ID: str = ""
    FACEBOOK_CLIENT_SECRET: str = ""
    OAUTH_REDIRECT_BASE: str = "http://localhost:3000"  # 前端網址（OAuth 完成後導回此處）
    BACKEND_URL: str = "http://localhost:8000"  # 後端網址（Google 回呼指向這裡）

    # AI / OCR
    ANTHROPIC_API_KEY: str = ""
    GEMINI_API_KEY: str = ""  # Google Gemini（免費，https://aistudio.google.com/apikey）
    GOOGLE_APPLICATION_CREDENTIALS: str = ""  # Google Vision 服務帳戶 JSON 路徑

    # LINE Notify (legacy, 已停用)
    LINE_CHANNEL_ACCESS_TOKEN: str = ""

    # LINE Login（OAuth）
    LINE_LOGIN_CHANNEL_ID: str = ""
    LINE_LOGIN_CHANNEL_SECRET: str = ""

    # LINE Messaging API（推播 + webhook）
    LINE_MESSAGING_TOKEN: str = ""        # Channel Access Token (long-lived)
    LINE_MESSAGING_SECRET: str = ""       # Channel Secret（用於驗證 webhook 簽章）
    LINE_OFFICIAL_ID: str = ""            # 官方帳號 LINE ID（如 @abc1234）給用戶加好友用

    # SMTP Email
    SMTP_HOST: str = ""
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    SMTP_FROM: str = "noreply@car-insurance.com"

    # Resend HTTP API（Render Free 層擋 SMTP，改走 HTTPS）
    RESEND_API_KEY: str = ""
    RESEND_FROM: str = "onboarding@resend.dev"  # 預設 sandbox，正式用要綁網域

    # App
    APP_NAME: str = "BOPINAN"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()

# JWT secret 強制檢查(沒設或設成範例值都會 raise / dev 環境會生隨機值)
settings.JWT_SECRET_KEY = _resolve_jwt_secret()

from pydantic_settings import BaseSettings
from typing import List
import json


class Settings(BaseSettings):
    # Database
    DATABASE_URL: str = "sqlite+aiosqlite:///./car_insurance.db"

    # JWT
    JWT_SECRET_KEY: str = "dev-secret-key-change-in-production"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 480
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
    OAUTH_REDIRECT_BASE: str = "http://localhost:3000"

    # AI / OCR
    ANTHROPIC_API_KEY: str = ""
    GEMINI_API_KEY: str = ""  # Google Gemini（免費，https://aistudio.google.com/apikey）
    GOOGLE_APPLICATION_CREDENTIALS: str = ""  # Google Vision 服務帳戶 JSON 路徑

    # LINE Notify
    LINE_CHANNEL_ACCESS_TOKEN: str = ""

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
    APP_NAME: str = "車險智能服務平台"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()

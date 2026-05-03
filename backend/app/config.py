from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    # Database
    DATABASE_URL: str = "sqlite+aiosqlite:///./car_insurance.db"

    # JWT
    JWT_SECRET_KEY: str = "dev-secret-key-change-in-production"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 480  # 8 小時（後台操作不用頻繁重登）
    REFRESH_TOKEN_EXPIRE_DAYS: int = 30

    # OTP
    OTP_EXPIRE_SECONDS: int = 300
    OTP_LENGTH: int = 6

    # CORS — 同時允許 localhost 與 127.0.0.1（瀏覽器視為不同 origin）
    CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ]

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

    # App
    APP_NAME: str = "車險智能服務平台"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()

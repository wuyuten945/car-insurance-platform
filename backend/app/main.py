from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
from datetime import datetime, timezone
from pathlib import Path
import uuid
import logging

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from app.config import settings
from app.database import create_tables
from app.routers import auth, customers, policies, renewal, accidents, claims, chatbot, notifications, rental, inspection, admin, oauth, admin_api, admin_console, line_bot
from app.tasks.policy_expiry_notifier import check_policy_expiry
from app.tasks.inspection_expiry_notifier import check_inspection_expiry

logger = logging.getLogger(__name__)

# APScheduler 實例
scheduler = AsyncIOScheduler()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    await create_tables()
    # 建立上傳目錄
    Path(settings.UPLOAD_DIR).mkdir(parents=True, exist_ok=True)

    # Render Free 層 ephemeral filesystem：DB 空時自動 seed（demo 用）
    try:
        import os
        if os.environ.get("AUTO_SEED", "0") == "1":
            from sqlalchemy import select
            from app.database import AsyncSessionLocal
            from app.models.user import User
            async with AsyncSessionLocal() as db:
                result = await db.execute(select(User).limit(1))
                if result.scalar_one_or_none() is None:
                    logger.info("DB 為空，執行 seed_data...")
                    import subprocess, sys
                    subprocess.run([sys.executable, "seed_data.py"], check=False)
                    logger.info("seed_data 完成")
    except Exception as e:
        logger.warning(f"auto-seed skipped: {e}")

    # 啟動排程：每日 09:00 檢查保單到期通知
    scheduler.add_job(
        check_policy_expiry,
        trigger=CronTrigger(hour=9, minute=0),
        id="policy_expiry_check",
        name="保單到期通知排程",
        replace_existing=True,
    )
    # 啟動排程：每日 09:30 檢查驗車到期通知
    scheduler.add_job(
        check_inspection_expiry,
        trigger=CronTrigger(hour=9, minute=30),
        id="inspection_expiry_check",
        name="驗車到期通知排程",
        replace_existing=True,
    )
    scheduler.start()
    logger.info("排程啟動：09:00 保單到期 / 09:30 驗車到期")

    print(f"\n{'='*60}")
    print(f"  {settings.APP_NAME} v{settings.APP_VERSION}")
    print(f"  API Docs: http://localhost:8000/docs")
    print(f"  排程: 09:00 保單到期通知 / 09:30 驗車到期通知")
    print(f"{'='*60}\n")
    yield
    # Shutdown
    scheduler.shutdown(wait=False)
    logger.info("排程已關閉")


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="BOPINAN API - AI-Powered Car Insurance Platform",
    lifespan=lifespan,
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Request ID middleware
@app.middleware("http")
async def add_request_id(request: Request, call_next):
    request_id = str(uuid.uuid4())
    request.state.request_id = request_id
    response = await call_next(request)
    response.headers["X-Request-ID"] = request_id
    return response


# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "data": None,
            "message": "伺服器內部錯誤" if not settings.DEBUG else str(exc),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        },
    )


# Mount static files for uploads
uploads_path = Path(settings.UPLOAD_DIR)
uploads_path.mkdir(parents=True, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=str(uploads_path)), name="uploads")

# Register routers
app.include_router(auth.router, prefix="/api/v1/auth", tags=["認證"])
app.include_router(customers.router, prefix="/api/v1/customers", tags=["客戶"])
app.include_router(policies.router, prefix="/api/v1/policies", tags=["保單"])
app.include_router(renewal.router, prefix="/api/v1/renewal", tags=["續保"])
app.include_router(accidents.router, prefix="/api/v1/accidents", tags=["事故"])
app.include_router(claims.router, prefix="/api/v1/claims", tags=["理賠"])
app.include_router(chatbot.router, prefix="/api/v1/chatbot", tags=["智能客服"])
app.include_router(notifications.router, prefix="/api/v1/notifications", tags=["通知"])
app.include_router(rental.router, prefix="/api/v1/rental-cars", tags=["代步車"])
app.include_router(oauth.router, prefix="/api/v1/oauth", tags=["社交登入"])
app.include_router(admin_api.router, prefix="/api/v1/admin-console", tags=["管理控制台API"])
app.include_router(admin.router, prefix="/admin", tags=["管理控制台"])
app.include_router(admin_console.router, prefix="/admin-console", tags=["管理控制台 UI"])
app.include_router(inspection.router, prefix="/api/v1/inspection-stations", tags=["驗車"])
app.include_router(line_bot.router, prefix="/api/v1/line-bot", tags=["LINE Bot"])


@app.get("/api/v1/health", tags=["系統"])
async def health_check():
    return {
        "success": True,
        "data": {
            "status": "healthy",
            "version": settings.APP_VERSION,
            "app": settings.APP_NAME,
        },
        "message": "系統運作正常",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@app.post("/api/v1/admin/trigger-expiry-check", tags=["系統"])
async def trigger_expiry_check():
    """手動觸發保單到期通知檢查（用於測試）"""
    await check_policy_expiry()
    return {
        "success": True,
        "data": None,
        "message": "保單到期通知檢查已執行",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@app.post("/api/v1/admin/trigger-inspection-check", tags=["系統"])
async def trigger_inspection_check():
    """手動觸發驗車到期通知檢查（用於測試）"""
    await check_inspection_expiry()
    return {
        "success": True,
        "data": None,
        "message": "驗車到期通知檢查已執行",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }

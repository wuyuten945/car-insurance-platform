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
from slowapi.errors import RateLimitExceeded

from app.config import settings
from app.core.rate_limit import limiter, _real_client_ip, _rate_limit_key
from app.core.rate_limit_log import record_hit as _record_rate_hit
from app.database import create_tables
from app.routers import auth, customers, policies, renewal, accidents, claims, chatbot, notifications, rental, inspection, admin, oauth, admin_api, admin_console, line_bot, quote_requests, numerology, billing
from app.tasks.policy_expiry_notifier import check_policy_expiry
from app.tasks.inspection_expiry_notifier import check_inspection_expiry
from app.tasks.subscription_expiry_notifier import check_subscription_expiry

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    force=True,  # 覆寫 uvicorn 已加的 handler，讓 app 內 logger.info 顯示
)
logger = logging.getLogger(__name__)

# APScheduler 實例
scheduler = AsyncIOScheduler()

# 速率限制器在 app/core/rate_limit.py 定義(讓 router 也能 import 來用 @limiter.limit())


async def _ensure_columns():
    """
    Idempotent 補欄位（schema migration light）。
    Base.metadata.create_all 不會 ALTER 現有表，因此新增 model 欄位後，
    要在此 EXPECTED 列表加一行讓既有部署自動補。
    SQLite 跟 PostgreSQL 都用 INFORMATION_SCHEMA / PRAGMA 偵測。
    """
    from sqlalchemy import text
    from app.database import engine
    EXPECTED = [
        # (table, column, ddl_for_postgres)
        ("users", "password_hash",   "VARCHAR(255)"),
        ("users", "is_line_friend",  "BOOLEAN NOT NULL DEFAULT FALSE"),
        ("users", "line_friend_at",  "TIMESTAMP WITH TIME ZONE"),
        ("user_vehicles", "manufacture_month", "INTEGER"),
        ("user_vehicles", "reissue_date",      "DATE"),
        ("policies",      "start_time",        "TIME"),
        ("policies",      "end_time",          "TIME"),
        ("policies",      "compulsory_start_date", "DATE"),
        ("policies",      "compulsory_end_date",   "DATE"),
        ("policies",      "compulsory_start_time", "TIME"),
        ("policies",      "compulsory_end_time",   "TIME"),
        ("policies",      "compulsory_insurer_name",  "VARCHAR(100)"),
        ("policies",      "compulsory_policy_number", "VARCHAR(50)"),
        ("policies",      "compulsory_premium",       "NUMERIC(12, 2)"),
        # 資料來源（business/self），舊資料一律視為 agent
        ("user_vehicles", "data_source", "VARCHAR(20) NOT NULL DEFAULT 'agent'"),
        ("policies",      "data_source", "VARCHAR(20) NOT NULL DEFAULT 'agent'"),
        # 通知偏好（提醒天數 CSV + email 開關）
        ("users",         "policy_notify_days",    "VARCHAR(64)"),
        ("users",         "inspection_notify_days","VARCHAR(64)"),
        ("users",         "notify_email_enabled",  "BOOLEAN NOT NULL DEFAULT FALSE"),
        # 要保人 / 被保人（保單獨立記錄；可能跟客戶 user 不同人）
        ("policies",      "policyholder_name",       "VARCHAR(100)"),
        ("policies",      "policyholder_id_number",  "VARCHAR(20)"),
        ("policies",      "policyholder_birth_date", "DATE"),
        ("policies",      "policyholder_gender",     "VARCHAR(10)"),
        ("policies",      "policyholder_phone",      "VARCHAR(20)"),
        ("policies",      "policyholder_relation_to_owner", "VARCHAR(50)"),
        # Token 版本(密碼變更/強制登出時 +1,JWT 比對 tv claim)
        ("users",         "token_version",   "INTEGER NOT NULL DEFAULT 0"),
        ("admin_users",   "token_version",   "INTEGER NOT NULL DEFAULT 0"),
        # 訂閱制(SUBSCRIPTION_SPEC.md)
        ("admin_users",   "subscription_status",     "VARCHAR(20) NOT NULL DEFAULT 'trial'"),
        ("admin_users",   "trial_started_at",        "TIMESTAMP WITH TIME ZONE"),
        ("admin_users",   "subscription_period_end", "TIMESTAMP WITH TIME ZONE"),
        ("admin_users",   "subscription_cancelled_at", "TIMESTAMP WITH TIME ZONE"),
        ("admin_users",   "subscription_price_twd",  "INTEGER NOT NULL DEFAULT 149"),
        ("admin_users",   "subscription_payment_ref","VARCHAR(100)"),
        ("policies",      "insured_name",       "VARCHAR(100)"),
        ("policies",      "insured_id_number",  "VARCHAR(20)"),
        ("policies",      "insured_birth_date", "DATE"),
        ("policies",      "insured_gender",     "VARCHAR(10)"),
        ("policies",      "insured_phone",      "VARCHAR(20)"),
    ]
    is_sqlite = "sqlite" in str(engine.url)
    try:
        async with engine.begin() as conn:
            for table, col, ddl in EXPECTED:
                if is_sqlite:
                    res = await conn.execute(text(f"PRAGMA table_info({table})"))
                    cols = {row[1] for row in res.fetchall()}
                    add_ddl = ddl.replace("BOOLEAN NOT NULL DEFAULT FALSE", "BOOLEAN NOT NULL DEFAULT 0") \
                                 .replace("TIMESTAMP WITH TIME ZONE", "DATETIME")
                else:
                    res = await conn.execute(text(
                        "SELECT column_name FROM information_schema.columns "
                        "WHERE table_name = :t"
                    ), {"t": table})
                    cols = {row[0] for row in res.fetchall()}
                    add_ddl = ddl
                if col not in cols:
                    await conn.execute(text(f"ALTER TABLE {table} ADD COLUMN {col} {add_ddl}"))
                    logger.info(f"[Schema] {table}.{col} 已補加")
    except Exception as e:
        logger.warning(f"[Schema] _ensure_columns 失敗: {e}")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    await create_tables()
    # 建立上傳目錄
    Path(settings.UPLOAD_DIR).mkdir(parents=True, exist_ok=True)

    # 自動補既有 DB 缺漏的欄位（idempotent）— Base.metadata.create_all 不會 ALTER 現有表
    # 因此每次新增 model 欄位後，要在這裡列出讓既有部署自動補
    await _ensure_columns()

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

    # 監理站 / 驗車廠 全台資料自動補：count < 20 時跑全台 100+ 站完整 seed
    # 不會清掉既有，只在資料明顯不足時補（給 Render PG 第一次啟動 / 之前只有 3 筆 minimal seed 的環境用）
    try:
        from sqlalchemy import select, func
        from app.database import AsyncSessionLocal
        from app.models.inspection import InspectionStation
        async with AsyncSessionLocal() as db:
            cnt = await db.execute(select(func.count()).select_from(InspectionStation))
            current = cnt.scalar() or 0
            if current < 20:
                logger.info(f"InspectionStation count = {current}，跑完整 seed_inspection_data ...")
                from app.tasks.seed_inspection_data import seed_inspection_data
                await seed_inspection_data()
                logger.info("inspection seed 完成")
    except Exception as e:
        logger.warning(f"inspection auto-seed skipped: {e}")

    # Bootstrap admin：env 設了 BOOTSTRAP_ADMIN_USERNAME + BOOTSTRAP_ADMIN_PASSWORD
    # 且該帳號不存在 → 自動建立 super_admin。Render ephemeral DB 重啟後也會重建。
    try:
        import os
        bootstrap_user = os.environ.get("BOOTSTRAP_ADMIN_USERNAME", "").strip()
        bootstrap_pwd = os.environ.get("BOOTSTRAP_ADMIN_PASSWORD", "")
        if bootstrap_user and bootstrap_pwd:
            from sqlalchemy import select
            from app.database import AsyncSessionLocal
            from app.models.admin_user import AdminUser
            from app.core.admin_auth import hash_password
            async with AsyncSessionLocal() as db:
                exists = await db.execute(select(AdminUser).where(AdminUser.username == bootstrap_user))
                if exists.scalar_one_or_none() is None:
                    admin = AdminUser(
                        username=bootstrap_user,
                        password_hash=hash_password(bootstrap_pwd),
                        display_name=bootstrap_user,
                        role="super_admin",
                        is_active=True,
                    )
                    db.add(admin)
                    await db.commit()
                    logger.info(f"[Bootstrap] 建立 super_admin: {bootstrap_user}")
                else:
                    logger.info(f"[Bootstrap] admin 已存在: {bootstrap_user}（略過）")
    except Exception as e:
        logger.warning(f"bootstrap admin 失敗: {e}")

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
    # 啟動排程：每日 09:45 檢查業務員訂閱到期
    scheduler.add_job(
        check_subscription_expiry,
        trigger=CronTrigger(hour=9, minute=45),
        id="subscription_expiry_check",
        name="訂閱到期通知排程",
        replace_existing=True,
    )
    scheduler.start()
    logger.info("排程啟動：09:00 保單 / 09:30 驗車 / 09:45 訂閱到期")

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

# 速率限制 — 必須在所有 router 前面註冊
app.state.limiter = limiter


# 自訂 rate-limit handler:除回 429 外,記錄誰被擋了多少次,給 admin 觀測用
async def _rate_limit_handler(request: Request, exc: RateLimitExceeded):
    try:
        _record_rate_hit(
            key=_rate_limit_key(request),
            path=str(request.url.path),
            method=request.method,
            ip=_real_client_ip(request),
            limit=str(exc.detail),
        )
    except Exception:
        pass
    return JSONResponse(
        status_code=429,
        content={
            "success": False,
            "data": None,
            "message": f"請求過於頻繁,請稍後再試 ({exc.detail})",
            "timestamp": datetime.now(timezone.utc).isoformat(),
        },
        headers={"Retry-After": "60"},
    )


app.add_exception_handler(RateLimitExceeded, _rate_limit_handler)

# CORS — 防呆:同時 allow_credentials=True 與 allow_origins=['*'] 是 CSRF 的 invitation,
# 偵測到就強制收斂為 [] 並警告
_cors_origins = settings.cors_origins_list
if _cors_origins == ["*"] or "*" in _cors_origins:
    logger.warning("[security] CORS_ORIGINS 含 '*' 與 allow_credentials=True 不可並存,強制收斂為空")
    _cors_origins = []
app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# 訂閱檢查 middleware:過期 agent 不能用大部分後台 endpoint
# 白名單(永遠開放):login / change-password / billing / admin html / static
_SUBSCRIPTION_EXEMPT_PREFIXES = (
    "/api/v1/admin-console/login",
    "/api/v1/admin-console/change-password",
    "/api/v1/billing/",
    "/admin",          # admin console html
    "/uploads/",       # 已 mount 的靜態檔
    "/openapi.json",
    "/docs",
    "/redoc",
)


@app.middleware("http")
async def check_subscription_gate(request: Request, call_next):
    path = request.url.path
    # 只擋 /api/v1/admin-console/* 開頭的 API,其他 path(客戶 API、auth、line 等)放行
    if not path.startswith("/api/v1/admin-console"):
        return await call_next(request)
    # 白名單放行
    if any(path.startswith(p) for p in _SUBSCRIPTION_EXEMPT_PREFIXES):
        return await call_next(request)

    # 解 token → 看 admin → 看訂閱狀態
    auth = request.headers.get("authorization", "")
    if not auth.startswith("Bearer "):
        return await call_next(request)   # 沒 token 留給 router 自己回 401
    token = auth[7:]
    try:
        from app.core.security import decode_token
        from app.services import subscription_service as _sub
        from app.database import AsyncSessionLocal
        from app.models.admin_user import AdminUser as _AU
        from sqlalchemy import select as _select

        payload = decode_token(token)
        if not payload or payload.get("type") != "admin":
            return await call_next(request)   # 無效 token 留給 router 處理 401

        async with AsyncSessionLocal() as db:
            result = await db.execute(_select(_AU).where(_AU.id == payload.get("sub")))
            admin = result.scalar_one_or_none()
            if admin is None:
                return await call_next(request)
            status = _sub.compute_status(admin)
            if not _sub.can_use_protected(status):
                return JSONResponse(
                    status_code=403,
                    content={
                        "success": False,
                        "data": {"subscription_status": status},
                        "message": "訂閱已過期,請至『訂閱』頁面續訂後再使用",
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                    },
                )
    except Exception as e:
        # middleware 內部錯誤不該擋 request,放行讓 router 處理(各 endpoint 仍有
        # Depends(get_current_admin) 做 token 驗證,所以這裡 fail-open 是安全的)。
        # 但要 log 出來,否則訂閱 gate 永遠繞過也不會被發現。
        logger.warning(f"[subscription-gate] middleware error: {type(e).__name__}: {e}")
    return await call_next(request)


# Request ID middleware
@app.middleware("http")
async def add_request_id(request: Request, call_next):
    request_id = str(uuid.uuid4())
    request.state.request_id = request_id
    response = await call_next(request)
    response.headers["X-Request-ID"] = request_id
    return response


# i18n middleware（依 Accept-Language 切換錯誤訊息語言）
from app.core.i18n import setup_i18n_middleware
setup_i18n_middleware(app)


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


# 自訂 StaticFiles:加上 X-Content-Type-Options: nosniff(防 SVG XSS / polyglot 檔)
class _SecureStaticFiles(StaticFiles):
    async def get_response(self, path, scope):
        response = await super().get_response(path, scope)
        response.headers.setdefault("X-Content-Type-Options", "nosniff")
        response.headers.setdefault("Content-Security-Policy", "default-src 'none'")
        response.headers.setdefault("Cache-Control", "private, max-age=300")
        return response


app.mount("/uploads", _SecureStaticFiles(directory=str(uploads_path)), name="uploads")

# Register routers
app.include_router(auth.router, prefix="/api/v1/auth", tags=["認證"])
app.include_router(customers.router, prefix="/api/v1/customers", tags=["客戶"])
app.include_router(policies.router, prefix="/api/v1/policies", tags=["保單"])
app.include_router(renewal.router, prefix="/api/v1/renewal", tags=["續保"])
app.include_router(accidents.router, prefix="/api/v1/accidents", tags=["事故"])
app.include_router(claims.router, prefix="/api/v1/claims", tags=["理賠"])
app.include_router(chatbot.router, prefix="/api/v1/chatbot", tags=["服務導引"])
app.include_router(notifications.router, prefix="/api/v1/notifications", tags=["通知"])
app.include_router(rental.router, prefix="/api/v1/rental-cars", tags=["代步車"])
app.include_router(oauth.router, prefix="/api/v1/oauth", tags=["社交登入"])
app.include_router(admin_api.router, prefix="/api/v1/admin-console", tags=["管理控制台API"])
app.include_router(admin.router, prefix="/admin", tags=["管理控制台"])
app.include_router(admin_console.router, prefix="/admin-console", tags=["管理控制台 UI"])
app.include_router(inspection.router, prefix="/api/v1/inspection-stations", tags=["驗車"])
app.include_router(line_bot.router, prefix="/api/v1/line-bot", tags=["LINE Bot"])
app.include_router(quote_requests.router, prefix="/api/v1/quote-requests", tags=["詢價工單"])
app.include_router(numerology.router, prefix="/api/v1/numerology", tags=["數字易經"])
app.include_router(billing.router, prefix="/api/v1/billing", tags=["訂閱"])


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

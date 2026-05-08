from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import DeclarativeBase
from datetime import datetime, timezone
from sqlalchemy import Column, DateTime, String
import uuid

from app.config import settings


def _normalize_db_url(url: str) -> str:
    """
    Render PostgreSQL Internal URL 格式為 'postgres://...'，需轉成 SQLAlchemy 認得的
    'postgresql+asyncpg://...' 才能用 async engine 連線。SQLite 不變。
    """
    if url.startswith("postgres://"):
        url = "postgresql+asyncpg://" + url[len("postgres://"):]
    elif url.startswith("postgresql://") and "+asyncpg" not in url:
        url = "postgresql+asyncpg://" + url[len("postgresql://"):]
    return url


_db_url = _normalize_db_url(settings.DATABASE_URL)
_is_sqlite = "sqlite" in _db_url

# 連線池調整:預設 5 個連線在負載一點點時就 queue。Render 免費 PG 上限 97 個 connection,
# 我們留充裕 buffer:pool_size=20 + max_overflow=10 = 同時 30 個。pool_pre_ping=True
# 確保撈到的 connection 是活的(避免 PG 自動 idle timeout 後第一次查詢失敗)。
# pool_recycle=1800 強制每 30 分鐘換一次連線,防 PG idle 太久被 kill。
_engine_kwargs = dict(echo=False)
if _is_sqlite:
    _engine_kwargs["connect_args"] = {"check_same_thread": False}
else:
    _engine_kwargs.update(
        pool_size=20,
        max_overflow=10,
        pool_pre_ping=True,
        pool_recycle=1800,
        pool_timeout=30,
    )

engine = create_async_engine(_db_url, **_engine_kwargs)

AsyncSessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


class TimestampMixin:
    # timezone=True 讓 PostgreSQL 用 TIMESTAMPTZ，可接受 aware/naive datetime；
    # SQLite 對 timezone=True 也相容（內部仍存 ISO 字串）。
    created_at = Column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )


def generate_uuid() -> str:
    return str(uuid.uuid4())


async def get_db():
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def create_tables():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

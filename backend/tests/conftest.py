"""
pytest fixtures。每個 test 跑在獨立 in-memory SQLite,不污染本地 dev DB。
"""
import os
import sys
from pathlib import Path

# 確保 backend root 在 sys.path,讓 'app.xxx' import 可解析
_BACKEND_ROOT = Path(__file__).parent.parent.resolve()
sys.path.insert(0, str(_BACKEND_ROOT))

# Test 用設定:強制 in-memory SQLite + dev mode + 一致 JWT secret
os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///:memory:"
os.environ["JWT_SECRET_KEY"] = "test-secret-key-test-test-test-test-32"
os.environ["DEBUG"] = "true"
os.environ.pop("RENDER", None)
os.environ.pop("RENDER_SERVICE_ID", None)

import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport


@pytest_asyncio.fixture
async def app_with_db():
    """每個 test 拿一份新 app + 新 in-memory DB(完全隔離)。"""
    # 延後 import,確保 env vars 已生效
    from app.main import app
    from app.database import create_tables
    await create_tables()
    yield app


@pytest_asyncio.fixture
async def client(app_with_db):
    """async test client 直連 ASGI app(不開真 HTTP server)。"""
    async with AsyncClient(transport=ASGITransport(app=app_with_db), base_url="http://test") as c:
        yield c

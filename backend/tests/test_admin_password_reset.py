"""
業務員/管理員「忘記密碼 → Email 重設連結」整合測試。

涵蓋:
  1. 正常流程:申請 → 收信 → 重設 → 新密碼可登入、舊密碼不行、舊登入 token 失效
  2. 不存在的帳號 / 沒登記 Email / 已停用:回應與正常一樣,但不寄信(防探測帳號)
  3. 連結只能用一次;竄改、過期、型別不對的 token 一律拒絕
  4. 新密碼太短被擋
  5. 同帳號每小時最多寄 3 封
"""
import re
import time

import pytest
import pytest_asyncio
from jose import jwt as jose_jwt

from app.config import settings
from app.core.admin_auth import hash_password, generate_api_key
from app.core.cache import cache
from app.database import AsyncSessionLocal
from app.models.admin_user import AdminUser


@pytest.fixture(autouse=True)
def _clean_cache():
    # 限流計數放在記憶體快取(單例),每個 test 前清空避免互相影響
    cache._store.clear()
    yield
    cache._store.clear()


@pytest_asyncio.fixture(autouse=True)
async def _dispose_engine():
    # 每個 test 結束關掉連線池:否則 aiosqlite 的連線 worker thread 留著,
    # 多個 test 一起跑時 pytest 跑完卻無法結束(行程卡在 threading._shutdown)
    yield
    from app.database import engine
    await engine.dispose()


@pytest.fixture
def outbox(monkeypatch):
    import app.core.email as email_module
    sent = []

    async def fake_send(to_email, subject, body):
        sent.append({"to": to_email, "subject": subject, "body": body})
        return True

    monkeypatch.setattr(email_module.email_service, "send", fake_send)
    return sent


async def _seed(username, email="agent@example.com", active=True, password="oldpass123"):
    async with AsyncSessionLocal() as db:
        a = AdminUser(username=username, password_hash=hash_password(password), display_name="測試業務",
                      email=email, role="agent", api_key=generate_api_key(), is_active=active, token_version=0)
        db.add(a)
        await db.commit()
        await db.refresh(a)
        return a


def _token_from(mail):
    m = re.search(r"/admin\?reset=([A-Za-z0-9_.-]+)", mail["body"])
    assert m, mail["body"]
    return m.group(1)


async def _login(client, username, password):
    r = await client.post("/api/v1/admin-console/login", json={"username": username, "password": password})
    return r.json()


@pytest.mark.asyncio
async def test_full_reset_flow(client, outbox):
    await _seed("agent_a")
    old_login = await _login(client, "agent_a", "oldpass123")
    old_token = old_login["data"]["token"]

    r = await client.post("/api/v1/admin-console/forgot-password", json={"account": "agent_a"})
    assert r.status_code == 200 and r.json()["success"] is True
    assert len(outbox) == 1 and outbox[0]["to"] == "agent@example.com"

    token = _token_from(outbox[0])
    r = await client.post("/api/v1/admin-console/reset-password", json={"token": token, "new_password": "newpass456"})
    assert r.status_code == 200, r.text

    assert (await _login(client, "agent_a", "newpass456"))["success"] is True
    assert (await _login(client, "agent_a", "oldpass123"))["success"] is False
    # 舊登入 token 因 token_version +1 失效
    r = await client.get("/api/v1/admin-console/customers", headers={"Authorization": f"Bearer {old_token}"})
    assert r.status_code in (401, 403)


@pytest.mark.asyncio
async def test_lookup_by_email(client, outbox):
    await _seed("agent_b", email="Bee@Example.com")
    r = await client.post("/api/v1/admin-console/forgot-password", json={"account": "bee@example.com"})
    assert r.status_code == 200
    assert [m["to"] for m in outbox] == ["Bee@Example.com"]


@pytest.mark.asyncio
async def test_no_enumeration(client, outbox):
    await _seed("agent_noemail", email=None)
    await _seed("agent_off", active=False)
    msgs = set()
    for acc in ("nobody_here", "agent_noemail", "agent_off"):
        r = await client.post("/api/v1/admin-console/forgot-password", json={"account": acc})
        assert r.status_code == 200
        msgs.add(r.json()["message"])
    assert len(msgs) == 1        # 三種情況回應完全一樣
    assert outbox == []          # 但都沒有寄信


@pytest.mark.asyncio
async def test_link_single_use(client, outbox):
    await _seed("agent_c")
    await client.post("/api/v1/admin-console/forgot-password", json={"account": "agent_c"})
    token = _token_from(outbox[0])
    r1 = await client.post("/api/v1/admin-console/reset-password", json={"token": token, "new_password": "first-new-1"})
    r2 = await client.post("/api/v1/admin-console/reset-password", json={"token": token, "new_password": "second-new-2"})
    assert r1.status_code == 200
    assert r2.status_code == 400
    assert (await _login(client, "agent_c", "first-new-1"))["success"] is True


@pytest.mark.asyncio
async def test_bad_tokens_rejected(client, outbox):
    a = await _seed("agent_d")
    await client.post("/api/v1/admin-console/forgot-password", json={"account": "agent_d"})
    good = _token_from(outbox[0])

    expired = jose_jwt.encode({"sub": a.id, "type": "admin_pwreset", "fp": jose_jwt.get_unverified_claims(good)["fp"],
                               "tv": 0, "exp": int(time.time()) - 10}, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
    wrong_type = jose_jwt.encode({"sub": a.id, "type": "admin", "tv": 0, "exp": int(time.time()) + 600},
                                 settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
    forged = jose_jwt.encode(jose_jwt.get_unverified_claims(good), "not-the-server-secret-xxxxxxxxxxxxxxx", algorithm="HS256")
    for bad in (expired, wrong_type, forged, good[:-3] + "abc", "garbage"):
        r = await client.post("/api/v1/admin-console/reset-password", json={"token": bad, "new_password": "whatever123"})
        assert r.status_code == 400, bad
    assert (await _login(client, "agent_d", "oldpass123"))["success"] is True  # 密碼沒被動到


@pytest.mark.asyncio
async def test_short_password_rejected(client, outbox):
    await _seed("agent_e")
    await client.post("/api/v1/admin-console/forgot-password", json={"account": "agent_e"})
    r = await client.post("/api/v1/admin-console/reset-password", json={"token": _token_from(outbox[0]), "new_password": "short"})
    assert r.status_code == 400
    assert (await _login(client, "agent_e", "oldpass123"))["success"] is True


@pytest.mark.asyncio
async def test_per_account_rate_limit(client, outbox):
    await _seed("agent_f")
    for _ in range(4):
        await client.post("/api/v1/admin-console/forgot-password", json={"account": "agent_f"})
    assert len(outbox) == 3

"""
前台客戶不得新增/修改保單（保單一律由業務員從後台建立）。

涵蓋:
  1. 新增保單、修改保單、上傳掃描、AI 辨識建檔 → 403
  2. 保障項目新增/修改/刪除 → 403（原本只檢查擁有者,連後台建檔的保單都能被客戶改）
  3. 刪除也不行(自填、後台建檔都一樣);仍可查看保單列表/明細
"""
from datetime import date, timedelta

import pytest
import pytest_asyncio

from app.core.cache import cache
from app.core.security import create_access_token
from app.database import AsyncSessionLocal
from app.models.policy import Policy, PolicyItem
from app.models.user import User


@pytest_asyncio.fixture(autouse=True)
async def _dispose_engine():
    cache._store.clear()
    yield
    from app.database import engine
    await engine.dispose()


async def _seed():
    async with AsyncSessionLocal() as db:
        u = User(email="cust@example.com", name="客戶")
        db.add(u)
        await db.flush()
        today = date.today()
        self_p = Policy(user_id=u.id, insurer_name="自填產險", policy_number="SELF-001", status="active",
                        start_date=today, end_date=today + timedelta(days=365), data_source="self")
        agent_p = Policy(user_id=u.id, insurer_name="富邦產險", policy_number="AGT-001", status="active",
                         start_date=today, end_date=today + timedelta(days=365), data_source="agent")
        db.add_all([self_p, agent_p])
        await db.flush()
        item = PolicyItem(policy_id=agent_p.id, item_name="車體損失險")
        db.add(item)
        await db.commit()
        return u.id, self_p.id, agent_p.id, item.id


def _auth(user_id):
    return {"Authorization": f"Bearer {create_access_token(user_id)}"}


NEW_POLICY = {"insurer_name": "某產險", "policy_number": "NEW-999",
              "start_date": str(date.today()), "end_date": str(date.today() + timedelta(days=365))}


@pytest.mark.asyncio
async def test_customer_cannot_create_or_edit(client):
    uid, self_id, agent_id, item_id = await _seed()
    h = _auth(uid)
    B = "/api/v1/policies"
    blocked = [
        await client.post(B, json=NEW_POLICY, headers=h),
        await client.put(f"{B}/{self_id}", json={"insurer_name": "改名"}, headers=h),
        await client.post(f"{B}/upload-scan", files={"file": ("p.png", b"\x89PNG\r\n\x1a\n" + b"0" * 64, "image/png")}, headers=h),
        await client.post(f"{B}/ocr-scan", params={"filename": "x.png"}, headers=h),
        await client.post(f"{B}/{agent_id}/items", json={"item_name": "竊盜險"}, headers=h),
        await client.put(f"{B}/{agent_id}/items/{item_id}", json={"item_name": "改掉"}, headers=h),
        await client.delete(f"{B}/{agent_id}/items/{item_id}", headers=h),
    ]
    for r in blocked:
        assert r.status_code == 403, (r.request.method, r.request.url, r.status_code, r.text)
        assert "業務員" in r.text

    # 資料沒有被動到
    r = await client.get(f"{B}/{agent_id}", headers=h)
    assert r.status_code == 200
    assert [i["item_name"] for i in r.json()["data"]["items"]] == ["車體損失險"]
    r = await client.get(B, headers=h)
    assert sorted(p["policy_number"] for p in r.json()["data"]) == ["AGT-001", "SELF-001"]


@pytest.mark.asyncio
async def test_customer_cannot_delete_any_policy(client):
    uid, self_id, agent_id, _ = await _seed()
    h = _auth(uid)
    for pid in (agent_id, self_id):             # 後台建檔、自己以前自填的都不能刪
        r = await client.delete(f"/api/v1/policies/{pid}", headers=h)
        assert r.status_code == 403, r.text
    r = await client.get("/api/v1/policies", headers=h)
    assert sorted(p["policy_number"] for p in r.json()["data"]) == ["AGT-001", "SELF-001"]

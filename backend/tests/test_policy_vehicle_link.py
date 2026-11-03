"""保單與行照（車輛）不可跨客戶混接；業務員新建的客戶歸到自己名下"""
from datetime import date, datetime, timedelta, timezone

import pytest

from app.core.admin_auth import hash_password, generate_api_key
from app.database import AsyncSessionLocal
from app.models.admin_user import AdminUser
from app.models.policy import Policy
from app.models.user import User
from app.models.vehicle import UserVehicle

from tests.test_dashboard import _h

API = "/api/v1/admin-console"


async def _seed(k):
    async with AsyncSessionLocal() as db:
        sup = AdminUser(username="boss" + k, password_hash=hash_password("x"), role="super_admin",
                        api_key=generate_api_key(), is_active=True, token_version=0)
        ag = AdminUser(username="ag" + k, display_name="張業務", password_hash=hash_password("x"), role="agent",
                       api_key=generate_api_key(), is_active=True, token_version=0,
                       subscription_status="trial", trial_started_at=datetime.now(timezone.utc),
                       subscription_period_end=datetime.now(timezone.utc) + timedelta(days=5))
        a = User(email=f"a{k}@example.com", name="甲")
        b = User(email=f"b{k}@example.com", name="乙")
        db.add_all([sup, ag, a, b])
        await db.flush()
        va = UserVehicle(user_id=a.id, plate_number="AAA-1111")
        vb = UserVehicle(user_id=b.id, plate_number="BBB-2222")
        db.add_all([va, vb])
        await db.commit()
        return sup, ag, a.id, b.id, va.id, vb.id


def _pol(num, vid):
    today = date.today()
    return {"insurer_name": "富邦產險", "policy_number": num, "vehicle_id": vid, "status": "active",
            "start_date": str(today), "end_date": str(today + timedelta(days=365)), "items": []}


@pytest.mark.asyncio
async def test_policy_vehicle_must_belong_to_customer(client):
    sup, ag, a, b, va, vb = await _seed("1")
    h = _h(sup)

    # 甲的保單掛乙的車 → 擋
    r = await client.post(f"{API}/customer/{a}/policies", headers=h, json=_pol("X-1", vb))
    assert r.status_code == 400, r.text
    # 甲的保單掛甲的車 → 可以
    r = await client.post(f"{API}/customer/{a}/policies", headers=h, json=_pol("X-2", va))
    assert r.status_code == 200, r.text
    pid = r.json()["data"]["id"]

    # 編輯時改掛乙的車 → 擋
    r = await client.put(f"{API}/policies/{pid}", headers=h, json={"vehicle_id": vb})
    assert r.status_code == 400, r.text

    # 保單轉給乙 → 甲的車不跟過去，連結解除
    r = await client.post(f"{API}/policies/{pid}/transfer", headers=h, json={"customer_id": b})
    assert r.status_code == 200, r.text
    assert r.json()["data"]["vehicle_unlinked"] == "AAA-1111"
    async with AsyncSessionLocal() as db:
        p = await db.get(Policy, pid)
        assert p.user_id == b and p.vehicle_id is None


@pytest.mark.asyncio
async def test_agent_created_customer_is_theirs(client):
    sup, ag, a, b, va, vb = await _seed("2")
    r = await client.post(f"{API}/customers", headers=_h(ag), json={"name": "丙"})
    assert r.status_code == 200, r.text
    cid = r.json()["data"]["id"]
    r = await client.get(f"{API}/customers", headers=_h(ag))
    ids = [c["id"] for c in r.json()["data"]]
    assert ids == [cid]
    # 建好就能直接幫他新增保單
    r = await client.post(f"{API}/customer/{cid}/policies", headers=_h(ag), json=_pol("X-3", None))
    assert r.status_code == 200, r.text


@pytest.mark.asyncio
async def test_link_check_lists_and_fixes(client):
    sup, ag, a, b, va, vb = await _seed("3")
    h = _h(sup)
    # 舊資料：甲的保單掛到乙的車（直接寫 DB 模擬上線前存錯的）
    today = date.today()
    async with AsyncSessionLocal() as db:
        p1 = Policy(user_id=a, vehicle_id=vb, insurer_name="富邦產險", policy_number="L-1", status="active",
                    start_date=today, end_date=today + timedelta(days=365))
        p2 = Policy(user_id=a, vehicle_id=vb, insurer_name="富邦產險", policy_number="L-2", status="active",
                    start_date=today, end_date=today + timedelta(days=365))
        ok = Policy(user_id=a, vehicle_id=va, insurer_name="富邦產險", policy_number="L-3", status="active",
                    start_date=today, end_date=today + timedelta(days=365))
        db.add_all([p1, p2, ok])
        await db.commit()
        p1id, p2id = p1.id, p2.id

    rows = (await client.get(f"{API}/link-check", headers=h)).json()["data"]
    mine = {r["policy_number"]: r for r in rows}
    assert set(mine) >= {"L-1", "L-2"} and "L-3" not in mine
    assert mine["L-1"]["customer_name"] == "甲" and mine["L-1"]["owner_name"] == "乙"
    assert mine["L-1"]["vehicle_plate"] == "BBB-2222"

    # 修法一：保單轉給車主 → 車輛連結保留
    r = await client.post(f"{API}/policies/{p1id}/transfer", headers=h, json={"customer_id": b})
    assert r.status_code == 200 and r.json()["data"]["vehicle_unlinked"] is None
    # 修法二：解除車輛連結 → 保單留在原客戶
    r = await client.put(f"{API}/policies/{p2id}", headers=h, json={"vehicle_id": None})
    assert r.status_code == 200, r.text
    rows = (await client.get(f"{API}/link-check", headers=h)).json()["data"]
    assert not {"L-1", "L-2"} & {r["policy_number"] for r in rows}
    async with AsyncSessionLocal() as db:
        assert (await db.get(Policy, p1id)).user_id == b
        p2 = await db.get(Policy, p2id)
        assert p2.user_id == a and p2.vehicle_id is None

    # 業務員只看得到自己客戶的保單
    r = await client.get(f"{API}/link-check", headers=_h(ag))
    assert r.status_code == 200 and r.json()["data"] == []

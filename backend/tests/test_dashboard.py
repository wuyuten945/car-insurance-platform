"""經營儀表板 /dashboard：彙整數字正確、業務員只看自己負責的客戶"""
from datetime import date, timedelta

import time
from datetime import datetime, timezone

import pytest

from jose import jwt as jose_jwt

from app.config import settings
from app.core.admin_auth import hash_password, generate_api_key
from app.database import AsyncSessionLocal
from app.models.admin_user import AdminUser, AgentCustomer
from app.models.policy import Policy
from app.models.user import User

API = "/api/v1/admin-console/dashboard"


async def _seed():
    async with AsyncSessionLocal() as db:
        sup = AdminUser(username="boss", password_hash=hash_password("x"), role="super_admin",
                        api_key=generate_api_key(), is_active=True, token_version=0)
        ag = AdminUser(username="ag1", display_name="張業務", password_hash=hash_password("x"), role="agent",
                       api_key=generate_api_key(), is_active=True, token_version=0,
                       subscription_status="trial", trial_started_at=datetime.now(timezone.utc),
                       subscription_period_end=datetime.now(timezone.utc) + timedelta(days=5))
        ag2 = AdminUser(username="ag2", display_name="李業務", password_hash=hash_password("x"), role="agent",
                        api_key=generate_api_key(), is_active=True, token_version=0,
                        subscription_status="trial", trial_started_at=datetime.now(timezone.utc),
                        subscription_period_end=datetime.now(timezone.utc) + timedelta(days=5))
        u1 = User(email="a@example.com", name="甲")
        u2 = User(email="b@example.com", name="乙")
        db.add_all([sup, ag, ag2, u1, u2])
        await db.flush()
        today = date.today()
        db.add_all([
            Policy(user_id=u1.id, insurer_name="富邦產險", policy_number="P1", status="active",
                   start_date=today, end_date=today + timedelta(days=20), total_premium=10000),
            Policy(user_id=u2.id, insurer_name="國泰產險", policy_number="P2", status="active",
                   start_date=today, end_date=today + timedelta(days=200), total_premium=5000),
            AgentCustomer(agent_id=ag.id, customer_id=u1.id),
        ])
        await db.commit()
        return sup, ag, ag2


def _h(a):
    tok = jose_jwt.encode({"sub": a.id, "type": "admin", "role": a.role, "tv": 0, "exp": int(time.time()) + 3600},
                          settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
    return {"Authorization": f"Bearer {tok}"}


@pytest.mark.asyncio
async def test_dashboard_super_and_agent(client):
    sup, ag, ag2 = await _seed()

    r = await client.get(API, headers=_h(sup))
    assert r.status_code == 200, r.text
    d = r.json()["data"]
    assert d["customers"]["total"] == 2
    assert d["policies"]["live_premium"] == 15000
    assert d["policies"]["due_30d"] == 1
    assert d["trend"][-1]["premium"] == 15000
    assert d["agents"][0]["name"] == "張業務" and d["agents"][0]["premium"] == 10000

    r = await client.get(API, headers=_h(ag))
    assert r.status_code == 200, r.text
    d = r.json()["data"]
    assert d["customers"]["total"] == 1
    assert d["policies"]["live_premium"] == 10000
    assert d["agents"] == []
    assert d["scope"] == "self" and d["owner"] == "張業務"

    # 另一位業務員沒有被分配客戶 → 看不到任何別人的資料
    r = await client.get(API, headers=_h(ag2))
    d = r.json()["data"]
    assert d["customers"]["total"] == 0
    assert d["policies"]["total"] == 0 and d["policies"]["live_premium"] == 0
    assert d["agents"] == []

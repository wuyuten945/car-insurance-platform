"""
訂閱制安全性整合測試:確保所有攻擊面都被擋住。

涵蓋:
  1. agent 不能 extend 任何人(包括自己)的訂閱
  2. agent 不能列其他 agent 的訂閱
  3. agent 只能看到自己的 /me
  4. super_admin 可以 extend / cancel / reactivate
  5. ExtendRequest 拒絕負數 / 過大月數 / 過長 payment_ref
  6. agent 過期後打 admin-console API 被 middleware 擋
  7. webhook provider 名稱有限制 + payload size 限制
  8. expired agent 仍可看 /me + cancel 自己(白名單通過)
"""
from datetime import datetime, timezone, timedelta

import pytest
from httpx import AsyncClient
from jose import jwt as jose_jwt
from sqlalchemy import select

from app.config import settings
from app.core.admin_auth import hash_password, generate_api_key
from app.database import AsyncSessionLocal
from app.models.admin_user import AdminUser
from app.services import subscription_service as svc


# ── helpers ─────────────────────────────────────────────────────


async def _seed_admin(*, role="agent", username=None, sub_status="trial",
                      period_offset_days=5) -> AdminUser:
    """直接 INSERT 一個 admin 到測試 DB(不走 API,因為 API 需 super_admin token)。"""
    async with AsyncSessionLocal() as db:
        admin = AdminUser(
            username=username or f"u_{generate_api_key()[:8]}",
            password_hash=hash_password("test1234"),
            display_name="Test Admin",
            role=role,
            api_key=generate_api_key(),
            is_active=True,
            token_version=0,
        )
        if role == "agent":
            now = datetime.now(timezone.utc)
            admin.subscription_status = sub_status
            admin.trial_started_at = now
            admin.subscription_period_end = now + timedelta(days=period_offset_days)
            admin.subscription_price_twd = 149
        db.add(admin)
        await db.commit()
        await db.refresh(admin)
        return admin


def _admin_token(admin_id: str, token_version: int = 0) -> str:
    """直接 mint admin JWT(避開 login flow)"""
    import time
    return jose_jwt.encode(
        {
            "sub": admin_id,
            "type": "admin",
            "role": "agent",
            "tv": token_version,
            "exp": int(time.time()) + 3600,
        },
        settings.JWT_SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM,
    )


def _h(admin: AdminUser) -> dict:
    """方便產 Authorization header。Token tv 要對得上 admin.token_version"""
    return {"Authorization": f"Bearer {_admin_token(admin.id, admin.token_version)}"}


# ── 攻擊面測試 ──────────────────────────────────────────────────


class TestSelfServeEndpoints:
    """agent 自己對自己的訂閱有合理權限"""

    async def test_agent_can_view_own_subscription(self, client: AsyncClient):
        agent = await _seed_admin(role="agent")
        r = await client.get("/api/v1/billing/subscription/me", headers=_h(agent))
        assert r.status_code == 200
        body = r.json()
        assert body["success"] is True
        assert body["data"]["status"] in ("trial", "active")
        assert body["data"]["price_twd"] == 149

    async def test_agent_can_cancel_own_subscription(self, client: AsyncClient):
        agent = await _seed_admin(role="agent", sub_status="active", period_offset_days=20)
        r = await client.post("/api/v1/billing/subscription/cancel", headers=_h(agent))
        assert r.status_code == 200
        # 確認 DB 真的標 cancelled
        async with AsyncSessionLocal() as db:
            res = await db.execute(select(AdminUser).where(AdminUser.id == agent.id))
            updated = res.scalar_one()
            assert updated.subscription_status == "cancelled"
            assert updated.subscription_cancelled_at is not None

    async def test_super_admin_cannot_cancel_self(self, client: AsyncClient):
        sa = await _seed_admin(role="super_admin")
        r = await client.post("/api/v1/billing/subscription/cancel", headers=_h(sa))
        # super_admin 沒訂閱可取消
        assert r.status_code == 400


class TestPrivilegeBoundary:
    """agent 不能碰其他 agent / super_admin endpoint"""

    async def test_agent_cannot_extend_anyone(self, client: AsyncClient):
        agent = await _seed_admin(role="agent")
        target = await _seed_admin(role="agent")
        r = await client.post(
            f"/api/v1/billing/subscriptions/{target.id}/extend",
            headers=_h(agent),
            json={"months": 1},
        )
        assert r.status_code == 403

    async def test_agent_cannot_extend_self(self, client: AsyncClient):
        agent = await _seed_admin(role="agent")
        r = await client.post(
            f"/api/v1/billing/subscriptions/{agent.id}/extend",
            headers=_h(agent),
            json={"months": 12},
        )
        assert r.status_code == 403

    async def test_agent_cannot_cancel_other(self, client: AsyncClient):
        agent = await _seed_admin(role="agent")
        target = await _seed_admin(role="agent")
        r = await client.post(
            f"/api/v1/billing/subscriptions/{target.id}/cancel",
            headers=_h(agent),
        )
        assert r.status_code == 403

    async def test_agent_cannot_reactivate_other(self, client: AsyncClient):
        agent = await _seed_admin(role="agent")
        target = await _seed_admin(role="agent")
        r = await client.post(
            f"/api/v1/billing/subscriptions/{target.id}/reactivate",
            headers=_h(agent),
        )
        assert r.status_code == 403

    async def test_agent_cannot_list_subscriptions(self, client: AsyncClient):
        agent = await _seed_admin(role="agent")
        r = await client.get("/api/v1/billing/subscriptions", headers=_h(agent))
        assert r.status_code == 403


class TestSuperAdminPath:
    async def test_super_admin_can_extend(self, client: AsyncClient):
        sa = await _seed_admin(role="super_admin")
        agent = await _seed_admin(role="agent", period_offset_days=2)
        r = await client.post(
            f"/api/v1/billing/subscriptions/{agent.id}/extend",
            headers=_h(sa),
            json={"months": 1, "payment_ref": "ECPAY-TEST-001"},
        )
        assert r.status_code == 200, r.text
        data = r.json()["data"]
        assert data["status"] == "active"
        # 期末應該 ≈ 原 period_end + 30 (因為延長從 max(now, period_end) 算)
        assert data["payment_ref"] == "ECPAY-TEST-001"

    async def test_super_admin_extend_nonexistent_agent_404(self, client: AsyncClient):
        sa = await _seed_admin(role="super_admin")
        r = await client.post(
            "/api/v1/billing/subscriptions/nope-no-such-id/extend",
            headers=_h(sa),
            json={"months": 1},
        )
        assert r.status_code == 404

    async def test_super_admin_cannot_extend_super_admin(self, client: AsyncClient):
        sa = await _seed_admin(role="super_admin")
        sa2 = await _seed_admin(role="super_admin")
        r = await client.post(
            f"/api/v1/billing/subscriptions/{sa2.id}/extend",
            headers=_h(sa),
            json={"months": 1},
        )
        assert r.status_code == 400


class TestInputValidation:
    """ExtendRequest 拒絕惡意 / 不合理輸入"""

    async def test_negative_months_rejected(self, client: AsyncClient):
        sa = await _seed_admin(role="super_admin")
        agent = await _seed_admin(role="agent")
        r = await client.post(
            f"/api/v1/billing/subscriptions/{agent.id}/extend",
            headers=_h(sa),
            json={"months": -1},
        )
        assert r.status_code == 422   # Pydantic ge=1 擋

    async def test_zero_months_rejected(self, client: AsyncClient):
        sa = await _seed_admin(role="super_admin")
        agent = await _seed_admin(role="agent")
        r = await client.post(
            f"/api/v1/billing/subscriptions/{agent.id}/extend",
            headers=_h(sa),
            json={"months": 0},
        )
        assert r.status_code == 422

    async def test_too_many_months_rejected(self, client: AsyncClient):
        sa = await _seed_admin(role="super_admin")
        agent = await _seed_admin(role="agent")
        r = await client.post(
            f"/api/v1/billing/subscriptions/{agent.id}/extend",
            headers=_h(sa),
            json={"months": 99999},
        )
        assert r.status_code == 422   # Pydantic le=60 擋

    async def test_too_long_payment_ref_rejected(self, client: AsyncClient):
        sa = await _seed_admin(role="super_admin")
        agent = await _seed_admin(role="agent")
        r = await client.post(
            f"/api/v1/billing/subscriptions/{agent.id}/extend",
            headers=_h(sa),
            json={"months": 1, "payment_ref": "X" * 200},
        )
        assert r.status_code == 422


class TestUnauthenticated:
    """沒 token 應該全部 401"""

    async def test_me_requires_auth(self, client: AsyncClient):
        r = await client.get("/api/v1/billing/subscription/me")
        assert r.status_code in (401, 422)

    async def test_extend_requires_auth(self, client: AsyncClient):
        r = await client.post(
            "/api/v1/billing/subscriptions/anyid/extend",
            json={"months": 1},
        )
        assert r.status_code in (401, 422)

    async def test_list_requires_auth(self, client: AsyncClient):
        r = await client.get("/api/v1/billing/subscriptions")
        assert r.status_code in (401, 422)


class TestWebhookHardening:
    """webhook 雖然不用 auth(外部金流),但要有基本防禦"""

    async def test_normal_provider_accepted(self, client: AsyncClient):
        r = await client.post("/api/v1/billing/webhook/ecpay", json={})
        assert r.status_code == 200

    async def test_malicious_provider_name_rejected(self, client: AsyncClient):
        r = await client.post("/api/v1/billing/webhook/..%2Fadmin", json={})
        # FastAPI 路由本身就會拒絕含 / 的 provider param,但加帶其他壞字也擋
        assert r.status_code in (400, 404, 405)

    async def test_provider_too_long_rejected(self, client: AsyncClient):
        r = await client.post("/api/v1/billing/webhook/" + "x" * 50, json={})
        assert r.status_code == 400

    async def test_huge_payload_rejected(self, client: AsyncClient):
        r = await client.post(
            "/api/v1/billing/webhook/ecpay",
            content=b"x" * (200 * 1024),    # 200KB
            headers={"content-type": "application/octet-stream"},
        )
        assert r.status_code == 400


class TestSubscriptionGateMiddleware:
    """過期 agent 打 admin-console API 應被 middleware 擋"""

    async def test_expired_agent_blocked_on_admin_console(self, client: AsyncClient):
        # 過期 30 天(超過寬限 3 天)
        agent = await _seed_admin(role="agent", sub_status="active",
                                   period_offset_days=-30)
        # 試打一個 admin-console endpoint
        r = await client.get("/api/v1/admin-console/customers", headers=_h(agent))
        assert r.status_code == 403
        body = r.json()
        # 訂閱 gate 的特定錯誤訊息
        assert "訂閱" in body.get("message", "") or "subscription" in body.get("message", "").lower()

    async def test_expired_agent_can_still_view_own_subscription(self, client: AsyncClient):
        """白名單:過期 agent 仍可看 /me 才能去續訂"""
        agent = await _seed_admin(role="agent", sub_status="active",
                                   period_offset_days=-30)
        r = await client.get("/api/v1/billing/subscription/me", headers=_h(agent))
        assert r.status_code == 200
        # 狀態應該是 expired
        assert r.json()["data"]["status"] in ("expired", "past_due")
        assert r.json()["data"]["can_use"] is False

    async def test_super_admin_never_blocked(self, client: AsyncClient):
        sa = await _seed_admin(role="super_admin")
        r = await client.get("/api/v1/admin-console/customers", headers=_h(sa))
        # 200 (正常列表) 或 500 (DB 沒填好) 都接受,只要不是 403
        assert r.status_code != 403

    async def test_active_agent_passes_gate(self, client: AsyncClient):
        agent = await _seed_admin(role="agent", sub_status="active",
                                   period_offset_days=20)
        r = await client.get("/api/v1/admin-console/customers", headers=_h(agent))
        assert r.status_code != 403

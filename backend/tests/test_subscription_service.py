"""
SubscriptionService 狀態邏輯單元測試。
不需要 DB,純測 compute_status / start_trial / extend_paid / cancel / reactivate。
"""
from datetime import datetime, timezone, timedelta
from types import SimpleNamespace

from app.services import subscription_service as svc


def _agent(**kw) -> SimpleNamespace:
    """產一個 mock AdminUser(role 預設 agent)"""
    defaults = dict(
        role="agent",
        subscription_status="trial",
        trial_started_at=None,
        subscription_period_end=None,
        subscription_cancelled_at=None,
        subscription_price_twd=149,
        subscription_payment_ref=None,
    )
    defaults.update(kw)
    return SimpleNamespace(**defaults)


_NOW = datetime(2026, 5, 8, 12, 0, tzinfo=timezone.utc)


class TestComputeStatus:
    def test_super_admin_always_super(self):
        a = _agent(role="super_admin")
        assert svc.compute_status(a, now=_NOW) == "super_admin"

    def test_trial_active_within_window(self):
        a = _agent(subscription_status="trial",
                   subscription_period_end=_NOW + timedelta(days=3))
        assert svc.compute_status(a, now=_NOW) == "trial"

    def test_trial_just_expired_within_grace(self):
        a = _agent(subscription_status="trial",
                   subscription_period_end=_NOW - timedelta(days=1))
        assert svc.compute_status(a, now=_NOW) == "past_due"

    def test_trial_after_grace_expired(self):
        a = _agent(subscription_status="trial",
                   subscription_period_end=_NOW - timedelta(days=10))
        assert svc.compute_status(a, now=_NOW) == "expired"

    def test_active_in_period(self):
        a = _agent(subscription_status="active",
                   subscription_period_end=_NOW + timedelta(days=15))
        assert svc.compute_status(a, now=_NOW) == "active"

    def test_active_just_past(self):
        a = _agent(subscription_status="active",
                   subscription_period_end=_NOW - timedelta(days=2))
        assert svc.compute_status(a, now=_NOW) == "past_due"

    def test_cancelled_with_remaining(self):
        a = _agent(subscription_status="cancelled",
                   subscription_period_end=_NOW + timedelta(days=10),
                   subscription_cancelled_at=_NOW - timedelta(days=2))
        assert svc.compute_status(a, now=_NOW) == "cancelled"

    def test_cancelled_after_grace_expired(self):
        a = _agent(subscription_status="cancelled",
                   subscription_period_end=_NOW - timedelta(days=10),
                   subscription_cancelled_at=_NOW - timedelta(days=15))
        assert svc.compute_status(a, now=_NOW) == "expired"

    def test_no_period_end_treated_as_expired(self):
        a = _agent(subscription_status="trial", subscription_period_end=None)
        assert svc.compute_status(a, now=_NOW) == "expired"


class TestCanUseProtected:
    def test_yes_for_super_trial_active_cancelled(self):
        for s in ("super_admin", "trial", "active", "cancelled"):
            assert svc.can_use_protected(s) is True

    def test_no_for_past_due_expired(self):
        for s in ("past_due", "expired"):
            assert svc.can_use_protected(s) is False


class TestStartTrial:
    def test_sets_period_end_7_days_out(self):
        a = _agent()
        svc.start_trial(a, now=_NOW)
        assert a.subscription_status == "trial"
        assert a.trial_started_at == _NOW
        assert a.subscription_period_end == _NOW + timedelta(days=7)

    def test_idempotent_does_not_restart(self):
        prev_started = _NOW - timedelta(days=3)
        prev_end = _NOW + timedelta(days=4)
        a = _agent(trial_started_at=prev_started, subscription_period_end=prev_end)
        svc.start_trial(a, now=_NOW)
        # 已啟動的 trial 不會被覆寫
        assert a.trial_started_at == prev_started
        assert a.subscription_period_end == prev_end


class TestExtendPaid:
    def test_extends_30_days_from_now_when_expired(self):
        a = _agent(subscription_status="expired",
                   subscription_period_end=_NOW - timedelta(days=10))
        svc.extend_paid(a, months=1, now=_NOW)
        assert a.subscription_status == "active"
        assert a.subscription_period_end == _NOW + timedelta(days=30)

    def test_stacks_on_existing_period(self):
        a = _agent(subscription_status="active",
                   subscription_period_end=_NOW + timedelta(days=10))
        svc.extend_paid(a, months=1, now=_NOW)
        # 現有期 + 30 天而非 now + 30 天
        assert a.subscription_period_end == _NOW + timedelta(days=40)

    def test_records_payment_ref(self):
        a = _agent()
        svc.extend_paid(a, months=2, payment_ref="ECPAY-XYZ-123", now=_NOW)
        assert a.subscription_payment_ref == "ECPAY-XYZ-123"
        assert a.subscription_period_end == _NOW + timedelta(days=60)

    def test_clears_cancelled_state(self):
        a = _agent(subscription_status="cancelled",
                   subscription_cancelled_at=_NOW - timedelta(days=2),
                   subscription_period_end=_NOW + timedelta(days=5))
        svc.extend_paid(a, months=1, now=_NOW)
        assert a.subscription_status == "active"
        assert a.subscription_cancelled_at is None


class TestCancel:
    def test_marks_cancelled_keeps_period_end(self):
        end = _NOW + timedelta(days=15)
        a = _agent(subscription_status="active", subscription_period_end=end)
        svc.cancel(a, now=_NOW)
        assert a.subscription_status == "cancelled"
        assert a.subscription_cancelled_at == _NOW
        assert a.subscription_period_end == end   # 不變


class TestReactivate:
    def test_reactivate_within_period(self):
        end = _NOW + timedelta(days=10)
        a = _agent(subscription_status="cancelled",
                   subscription_cancelled_at=_NOW - timedelta(days=1),
                   subscription_period_end=end)
        svc.reactivate(a, now=_NOW)
        assert a.subscription_status == "active"
        assert a.subscription_cancelled_at is None
        assert a.subscription_period_end == end

    def test_reactivate_after_period_treats_as_extend(self):
        a = _agent(subscription_status="cancelled",
                   subscription_period_end=_NOW - timedelta(days=5))
        svc.reactivate(a, now=_NOW)
        # 過期後重啟應視同新付一個月
        assert a.subscription_status == "active"
        assert a.subscription_period_end == _NOW + timedelta(days=30)

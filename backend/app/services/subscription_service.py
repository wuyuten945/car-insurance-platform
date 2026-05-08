"""
訂閱制核心邏輯 — provider-agnostic,可獨立抽出做 microservice。

詳見 SUBSCRIPTION_SPEC.md。
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone, timedelta

from app.models.admin_user import AdminUser

TRIAL_DAYS = 7
DEFAULT_PRICE_TWD = 149
GRACE_DAYS = 3              # 期末過期後的寬限天數(避開繳費 race)
PAID_PERIOD_DAYS = 30


@dataclass
class SubscriptionView:
    """API 回應用的純資料 DTO。"""
    status: str               # trial / active / past_due / cancelled / expired / super_admin
    period_end: str | None    # ISO datetime 或 None
    days_remaining: int | None
    price_twd: int
    can_use: bool             # 目前能不能使用受保護的功能
    is_cancelled: bool
    cancelled_at: str | None
    payment_ref: str | None


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _aware(dt: datetime | None) -> datetime | None:
    """確保 datetime 是 timezone-aware(SQLite + 老資料可能是 naive)。"""
    if dt is None:
        return None
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt


def compute_status(admin: AdminUser, *, now: datetime | None = None) -> str:
    """即時計算訂閱狀態(不寫 DB,可在每次 request 跑)。

    回傳:
      - super_admin: super_admin 永遠不被訂閱限制
      - trial: 試用中
      - active: 已付費,期內
      - past_due: 期末過了寬限期(封鎖)
      - cancelled: 已取消但 period_end 還沒到(可繼續用)
      - expired: 沒記錄,或結束狀態
    """
    if admin.role == "super_admin":
        return "super_admin"

    now = now or _now()
    period_end = _aware(getattr(admin, "subscription_period_end", None))
    raw_status = getattr(admin, "subscription_status", None) or "trial"

    if raw_status == "cancelled":
        # 取消後仍可使用直到 period_end + 寬限
        if period_end and now < period_end + timedelta(days=GRACE_DAYS):
            return "cancelled"
        return "expired"

    if raw_status in ("trial", "active"):
        if period_end is None:
            # 未設過期日:視為 trial 結束(理論上不該發生)
            return "expired"
        if now < period_end:
            return raw_status
        # 過了 period_end → 看寬限
        if now < period_end + timedelta(days=GRACE_DAYS):
            return "past_due"
        return "expired"

    if raw_status == "past_due":
        if period_end and now < period_end + timedelta(days=GRACE_DAYS):
            return "past_due"
        return "expired"

    # 任何其他狀態都當成 expired
    return "expired"


def can_use_protected(status: str) -> bool:
    """status 對應的「能否使用受保護功能」決策。"""
    return status in ("super_admin", "trial", "active", "cancelled")


def days_remaining(admin: AdminUser, *, now: datetime | None = None) -> int | None:
    """目前訂閱還能用幾天(含寬限)。super_admin 回 None。"""
    if admin.role == "super_admin":
        return None
    now = now or _now()
    period_end = _aware(getattr(admin, "subscription_period_end", None))
    if period_end is None:
        return 0
    delta = (period_end + timedelta(days=GRACE_DAYS)) - now
    return max(0, int(delta.total_seconds() // 86400))


def to_view(admin: AdminUser, *, now: datetime | None = None) -> SubscriptionView:
    now = now or _now()
    status = compute_status(admin, now=now)
    period_end = _aware(getattr(admin, "subscription_period_end", None))
    cancelled_at = _aware(getattr(admin, "subscription_cancelled_at", None))
    return SubscriptionView(
        status=status,
        period_end=period_end.isoformat() if period_end else None,
        days_remaining=days_remaining(admin, now=now),
        price_twd=int(getattr(admin, "subscription_price_twd", DEFAULT_PRICE_TWD) or DEFAULT_PRICE_TWD),
        can_use=can_use_protected(status),
        is_cancelled=bool(cancelled_at),
        cancelled_at=cancelled_at.isoformat() if cancelled_at else None,
        payment_ref=getattr(admin, "subscription_payment_ref", None),
    )


# ─────────────────────────────────────────────────────────────
# 狀態變更 (寫 DB 的操作 — 由 router 在 transaction 內呼叫)
# ─────────────────────────────────────────────────────────────


def start_trial(admin: AdminUser, *, days: int = TRIAL_DAYS, now: datetime | None = None) -> None:
    """新建 agent 時呼叫。如果已經有 trial_started_at 就 skip(不重啟試用)。"""
    if getattr(admin, "trial_started_at", None) is not None:
        return
    now = now or _now()
    admin.subscription_status = "trial"
    admin.trial_started_at = now
    admin.subscription_period_end = now + timedelta(days=days)
    admin.subscription_cancelled_at = None
    admin.subscription_price_twd = admin.subscription_price_twd or DEFAULT_PRICE_TWD


def extend_paid(
    admin: AdminUser,
    *,
    months: int = 1,
    payment_ref: str | None = None,
    now: datetime | None = None,
) -> None:
    """付費延長。從 max(now, current period_end) 加 30*months 天。"""
    now = now or _now()
    months = max(1, int(months))
    base = max(now, _aware(admin.subscription_period_end) or now)
    admin.subscription_period_end = base + timedelta(days=PAID_PERIOD_DAYS * months)
    admin.subscription_status = "active"
    admin.subscription_cancelled_at = None  # 延長即解除取消狀態
    if payment_ref:
        admin.subscription_payment_ref = payment_ref


def cancel(admin: AdminUser, *, now: datetime | None = None) -> None:
    """取消訂閱。period_end 不變,使用到當期結束。"""
    now = now or _now()
    admin.subscription_status = "cancelled"
    admin.subscription_cancelled_at = now


def reactivate(admin: AdminUser, *, now: datetime | None = None) -> None:
    """重啟取消的訂閱(period 還沒過時用)。"""
    now = now or _now()
    period_end = _aware(admin.subscription_period_end)
    if period_end is None or now >= period_end:
        # 期已過 → 等同於從現在算 30 天
        extend_paid(admin, months=1, now=now)
        return
    admin.subscription_status = "active"
    admin.subscription_cancelled_at = None

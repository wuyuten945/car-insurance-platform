"""
訂閱到期前提醒(每日 09:45 跑)。

提醒對象:
  - 試用中,剩 ≤ 2 天 → email 提醒「快試用結束」
  - 已訂閱(active),剩 ≤ 3 天 → email 提醒「即將到期」
  - 過期當天(進入 past_due) → email 通知 super_admin + agent
"""
from __future__ import annotations

import logging
from datetime import datetime, timezone, timedelta

from sqlalchemy import select

from app.database import AsyncSessionLocal
from app.models.admin_user import AdminUser
from app.services import subscription_service as svc
from app.core.email import email_service

logger = logging.getLogger(__name__)


def _days_until(period_end: datetime | None, now: datetime) -> int | None:
    if period_end is None:
        return None
    if period_end.tzinfo is None:
        period_end = period_end.replace(tzinfo=timezone.utc)
    delta = period_end - now
    return int(delta.total_seconds() // 86400)


async def check_subscription_expiry() -> None:
    """每日跑一次。對接近到期的 agent 寄通知。"""
    now = datetime.now(timezone.utc)
    notified = 0
    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(AdminUser).where(AdminUser.role == "agent", AdminUser.is_active.is_(True))
        )
        agents = result.scalars().all()
        for agent in agents:
            status = svc.compute_status(agent, now=now)
            days = _days_until(agent.subscription_period_end, now)
            email = (agent.email or "").strip()
            if not email:
                continue

            try:
                if status == "trial" and days is not None and 0 <= days <= 2:
                    await _send_trial_reminder(email, agent, days)
                    notified += 1
                elif status == "active" and days is not None and 0 <= days <= 3:
                    await _send_renewal_reminder(email, agent, days)
                    notified += 1
                elif status == "past_due":
                    # 進入寬限期當天通知一次(用 days = -1 ~ -3 區間判斷)
                    if days is not None and -1 >= days >= -3:
                        await _send_past_due_alert(email, agent, days)
                        notified += 1
            except Exception as e:
                logger.warning(f"[sub-expiry] 寄信給 {email} 失敗: {e}")

    if notified:
        logger.info(f"[sub-expiry] 已通知 {notified} 位 agent")


async def _send_trial_reminder(email: str, agent: AdminUser, days: int) -> None:
    subj = f"【BOPINAN】試用還剩 {days} 天,記得訂閱"
    html = f"""
<p>{agent.display_name or agent.username} 您好,</p>
<p>您的 BOPINAN 業務員後台 <b>免費試用</b>還剩 <b>{days}</b> 天。</p>
<p>試用結束後若未訂閱,大部分後台功能將被停用。月費僅 <b>NT$149</b>,
請聯繫您的 super_admin / 管理員完成訂閱。</p>
<p>如已完成付款,請忽略此信。</p>
"""
    await email_service.send(email, subj, html)


async def _send_renewal_reminder(email: str, agent: AdminUser, days: int) -> None:
    subj = f"【BOPINAN】訂閱還剩 {days} 天,即將到期"
    html = f"""
<p>{agent.display_name or agent.username} 您好,</p>
<p>您的 BOPINAN 訂閱即將在 <b>{days}</b> 天後到期。為了不影響您的後台使用,
請於到期前完成下個月份(NT$149)的付款。</p>
<p>如已完成付款,請忽略此信。</p>
"""
    await email_service.send(email, subj, html)


async def _send_past_due_alert(email: str, agent: AdminUser, days: int) -> None:
    subj = "【BOPINAN】訂閱已過期,寬限期內"
    html = f"""
<p>{agent.display_name or agent.username} 您好,</p>
<p>您的 BOPINAN 訂閱已過期 {abs(days)} 天,目前處於 3 天寬限期。</p>
<p><b>過了寬限期後大部分後台功能會被停用</b>,請盡快聯繫管理員完成續訂。</p>
"""
    await email_service.send(email, subj, html)

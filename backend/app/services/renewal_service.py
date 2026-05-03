from datetime import date, timedelta
from decimal import Decimal
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from app.models.policy import Policy, RenewalQuote
from app.services.notification_service import NotificationService


# 續保提醒時程（天數）
REMINDER_DAYS = [60, 30, 14, 7, 3, 1, 0, -1]

REMINDER_MESSAGES = {
    60: ("續保提醒", "您的{insurer}保單（{policy_number}）將於 {end_date} 到期，建議開始準備續保。"),
    30: ("續保詳細資訊", "您的保單將於 {end_date} 到期，已為您準備多家保險公司報價比較，請前往查看。"),
    14: ("緊急續保提醒", "您的保單即將於 {end_date} 到期，請儘速完成續保，避免保障中斷。"),
    7: ("保單到期倒數 {days} 天", "您的保單將於 {end_date} 到期，請立即前往續保。"),
    3: ("保單到期倒數 {days} 天 - 強制責任險警示", "您的保單即將到期，強制責任險失效後將無法合法上路，請立即續保！"),
    1: ("保單明天到期！", "您的保單明天到期，請今天完成續保！過期後將失去保障。"),
    0: ("保單今日到期", "您的保單今天到期，請立即續保以避免保障中斷。"),
    -1: ("保單已過期", "您的保單已於昨天到期，目前處於無保障狀態，請儘速投保。"),
}

# Mock 保險公司資料
MOCK_INSURERS = [
    {"name": "富邦產險", "logo": "/images/insurers/fubon.png", "rating": 4.5, "speed": 5.2, "features": "24小時道路救援、免費代步車3天"},
    {"name": "國泰產險", "logo": "/images/insurers/cathay.png", "rating": 4.3, "speed": 4.8, "features": "線上理賠快速通道、保費分期0利率"},
    {"name": "新光產險", "logo": "/images/insurers/shinkong.png", "rating": 4.1, "speed": 6.0, "features": "首年優惠85折、道路救援無限次"},
    {"name": "明台產險", "logo": "/images/insurers/msig.png", "rating": 4.4, "speed": 4.5, "features": "保費最低價保證、快速理賠48小時"},
    {"name": "泰安產險", "logo": "/images/insurers/taian.png", "rating": 4.0, "speed": 5.5, "features": "網路投保9折、多車優惠方案"},
]


class RenewalService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def check_and_send_reminders(self) -> int:
        """檢查所有即將到期的保單並發送提醒（排程任務呼叫）"""
        today = date.today()
        sent_count = 0
        notification_svc = NotificationService(self.db)

        for days in REMINDER_DAYS:
            target_date = today + timedelta(days=days)
            result = await self.db.execute(
                select(Policy).where(
                    and_(Policy.end_date == target_date, Policy.status.in_(["active", "expiring"]))
                )
            )
            policies = result.scalars().all()

            for policy in policies:
                title_template, body_template = REMINDER_MESSAGES.get(days, ("續保提醒", "您的保單即將到期"))
                title = title_template.format(days=days)
                body = body_template.format(
                    insurer=policy.insurer_name,
                    policy_number=policy.policy_number,
                    end_date=policy.end_date.strftime("%Y-%m-%d"),
                    days=days,
                )

                await notification_svc.create_notification(
                    user_id=policy.user_id,
                    title=title,
                    body=body,
                    notification_type="renewal_reminder",
                    reference_type="policy",
                    reference_id=policy.id,
                )
                sent_count += 1

                if policy.status == "active" and days <= 30:
                    policy.status = "expiring"

        return sent_count

    async def generate_quotes(self, policy_id: str) -> list[RenewalQuote]:
        """為保單生成續保報價（Mock 資料）"""
        result = await self.db.execute(
            select(Policy).where(Policy.id == policy_id)
        )
        policy = result.scalar_one_or_none()
        if not policy:
            return []

        # 清除舊報價
        old_quotes = await self.db.execute(
            select(RenewalQuote).where(RenewalQuote.policy_id == policy_id)
        )
        for q in old_quotes.scalars().all():
            await self.db.delete(q)

        import random
        base_premium = float(policy.total_premium or 15000)
        quotes = []
        valid_until = date.today() + timedelta(days=14)

        for insurer in MOCK_INSURERS:
            variation = random.uniform(0.85, 1.15)
            quoted = round(base_premium * variation, 0)
            quote = RenewalQuote(
                policy_id=policy_id,
                insurer_name=insurer["name"],
                insurer_logo_url=insurer["logo"],
                quoted_premium=Decimal(str(quoted)),
                coverage_details={"items": ["強制責任險", "第三人責任險", "車體損失險"]},
                rating=Decimal(str(insurer["rating"])),
                claim_speed_days=Decimal(str(insurer["speed"])),
                features=insurer["features"],
                valid_until=valid_until,
            )
            self.db.add(quote)
            quotes.append(quote)

        await self.db.flush()
        return quotes

"""
保單到期通知排程任務

- 到期前 2 個月：第一次提醒（建議開始比價）
- 到期前 1 個月：第二次提醒（緊急提醒儘速續保）

通知管道：站內通知 + LINE + Email + SMS
每日 09:00 執行一次
"""
import logging
from datetime import date, timedelta, datetime, timezone

from sqlalchemy import select, and_, not_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database import AsyncSessionLocal
from app.models.policy import Policy
from app.models.notification import Notification
from app.models.user import User
from app.core.sms import sms_gateway
from app.core.email import email_service
from app.core.line import line_service

logger = logging.getLogger(__name__)


async def check_policy_expiry():
    """每日排程：檢查即將到期的保單，發送多管道通知"""
    today = date.today()
    two_months_later = today + timedelta(days=60)
    one_month_later = today + timedelta(days=30)

    logger.info(f"[排程] 開始檢查保單到期通知 - {today}")
    print(f"\n[排程] 檢查保單到期通知 - {today}")

    async with AsyncSessionLocal() as db:
        try:
            # 查詢所有有效保單，載入 user 關聯
            result = await db.execute(
                select(Policy)
                .options(selectinload(Policy.user))
                .where(
                    and_(
                        Policy.status.in_(["active", "expiring"]),
                        Policy.end_date >= today,
                        Policy.end_date <= two_months_later,
                    )
                )
            )
            policies = list(result.scalars().all())

            if not policies:
                logger.info("[排程] 目前沒有即將到期的保單")
                print("   [OK] 目前沒有即將到期的保單")
                return

            for policy in policies:
                days_left = (policy.end_date - today).days
                user = policy.user
                if not user:
                    continue

                # 判斷通知類型
                if 28 <= days_left <= 32:
                    # 到期前 1 個月
                    await _send_expiry_notification(
                        db, user, policy, days_left,
                        level="urgent",
                        notification_key=f"expiry_1m_{policy.id}_{policy.end_date}",
                    )
                elif 58 <= days_left <= 62:
                    # 到期前 2 個月
                    await _send_expiry_notification(
                        db, user, policy, days_left,
                        level="early",
                        notification_key=f"expiry_2m_{policy.id}_{policy.end_date}",
                    )

            await db.commit()
            logger.info(f"[排程] 保單到期通知檢查完成")
            print("   [OK] 保單到期通知檢查完成\n")

        except Exception as e:
            await db.rollback()
            logger.error(f"[排程] 保單到期通知失敗: {e}")
            print(f"   [ERROR] 保單到期通知失敗: {e}\n")


async def _send_expiry_notification(
    db: AsyncSession,
    user: User,
    policy: Policy,
    days_left: int,
    level: str,
    notification_key: str,
):
    """
    發送到期通知（多管道）

    level:
      - "early": 到期前 2 個月，溫和提醒
      - "urgent": 到期前 1 個月，緊急提醒
    """
    # 檢查是否已發送過同類通知（避免重複）
    existing = await db.execute(
        select(Notification).where(
            and_(
                Notification.user_id == user.id,
                Notification.reference_id == policy.id,
                Notification.notification_type == "renewal_reminder",
                Notification.body.contains(notification_key),
            )
        )
    )
    if existing.scalar_one_or_none():
        return  # 已發送過，跳過

    user_name = user.name or "客戶"
    end_date_str = policy.end_date.strftime("%Y/%m/%d")

    countdown = f"（倒數 {days_left} 天）" if days_left > 0 else "（今日到期）"

    if level == "urgent":
        title = f"[緊急] 保單倒數 {days_left} 天 - {policy.policy_number}"
        body = (
            f"{user_name} 您好，\n"
            f"您的 {policy.insurer_name} 保單（{policy.policy_number}）"
            f"將於 {end_date_str} 到期{countdown}。\n"
            f"請儘速完成續保，避免車輛處於無保障狀態。\n"
            f"前往續保比價：https://localhost:3000/renewal?policy_id={policy.id}"
        )
        sms_msg = (
            f"[車險平台]保單{policy.policy_number} "
            f"{end_date_str}到期{countdown}，請儘速續保。"
        )
        email_subject = f"[緊急] 保單 {policy.policy_number} 倒數 {days_left} 天"
    else:
        title = f"[提醒] 保單倒數 {days_left} 天 - {policy.policy_number}"
        body = (
            f"{user_name} 您好，\n"
            f"您的 {policy.insurer_name} 保單（{policy.policy_number}）"
            f"將於 {end_date_str} 到期{countdown}。\n"
            f"建議您提早比較續保方案，確保最佳保障與費率。\n"
            f"前往續保比價：https://localhost:3000/renewal?policy_id={policy.id}"
        )
        sms_msg = (
            f"[車險平台]保單{policy.policy_number} "
            f"{end_date_str}到期{countdown}，建議提早續保。"
        )
        email_subject = f"[提醒] 保單 {policy.policy_number} 倒數 {days_left} 天"

    # 內含 notification_key 以便查重
    body_with_key = f"{body}\n<!-- {notification_key} -->"

    email_body = _build_email_html(user_name, policy, days_left, level)

    # 1. 站內通知
    notification = Notification(
        user_id=user.id,
        title=title,
        body=body_with_key,
        notification_type="renewal_reminder",
        reference_type="policy",
        reference_id=policy.id,
        channel="multi",
    )
    db.add(notification)

    # 2. SMS 通知
    if user.phone:
        await sms_gateway.send(user.phone, sms_msg)
        logger.info(f"[排程] SMS 已發送: {user.phone} - {policy.policy_number}")

    # 3. Email 通知
    if user.email:
        await email_service.send(user.email, email_subject, email_body)
        logger.info(f"[排程] Email 已發送: {user.email} - {policy.policy_number}")

    # 4. LINE 通知
    line_msg = f"{title}\n\n{body}"
    await line_service.send(user.id, line_msg)
    logger.info(f"[排程] LINE 已發送: {user.id} - {policy.policy_number}")

    # 更新保單狀態為 expiring
    if level == "urgent" and policy.status == "active":
        policy.status = "expiring"

    print(f"   [NOTIFY][{level.upper()}] {user_name} - {policy.policy_number} 到期日 {end_date_str} (剩{days_left}天)")
    print(f"      -> 站內通知 OK | SMS({user.phone or 'N/A'}) OK | Email({user.email or 'N/A'}) OK | LINE OK")


def _build_email_html(user_name: str, policy: Policy, days_left: int, level: str) -> str:
    """產生 HTML 格式的 Email 內容"""
    end_date_str = policy.end_date.strftime("%Y/%m/%d")
    color = "#D32F2F" if level == "urgent" else "#1565C0"
    urgency = "緊急" if level == "urgent" else "提醒"

    return f"""
    <html>
    <body style="font-family: 'Microsoft JhengHei', Arial, sans-serif; max-width: 600px; margin: 0 auto;">
        <div style="background: {color}; color: white; padding: 20px; border-radius: 12px 12px 0 0;">
            <h2 style="margin: 0;">BOPINAN</h2>
            <p style="margin: 8px 0 0;">保單到期{urgency}通知</p>
        </div>
        <div style="padding: 24px; border: 1px solid #e0e0e0; border-top: none; border-radius: 0 0 12px 12px;">
            <p>{user_name} 您好，</p>
            <p>您的車險保單即將到期，請注意以下資訊：</p>
            <table style="width: 100%; border-collapse: collapse; margin: 16px 0;">
                <tr style="border-bottom: 1px solid #eee;">
                    <td style="padding: 8px; color: #666;">保險公司</td>
                    <td style="padding: 8px; font-weight: bold;">{policy.insurer_name}</td>
                </tr>
                <tr style="border-bottom: 1px solid #eee;">
                    <td style="padding: 8px; color: #666;">保單號碼</td>
                    <td style="padding: 8px; font-weight: bold;">{policy.policy_number}</td>
                </tr>
                <tr style="border-bottom: 1px solid #eee;">
                    <td style="padding: 8px; color: #666;">到期日期</td>
                    <td style="padding: 8px; font-weight: bold; color: {color};">{end_date_str}</td>
                </tr>
                <tr>
                    <td style="padding: 8px; color: #666;">剩餘天數</td>
                    <td style="padding: 8px; font-weight: bold; color: {color};">{days_left} 天</td>
                </tr>
            </table>
            <a href="https://localhost:3000/renewal?policy_id={policy.id}"
               style="display: inline-block; background: {color}; color: white; padding: 12px 24px;
                      border-radius: 8px; text-decoration: none; font-weight: bold; margin-top: 8px;">
                立即續保比價
            </a>
            <p style="color: #999; font-size: 12px; margin-top: 24px;">
                此為系統自動發送，請勿直接回覆此信件。<br>
                BOPINAN | 客服專線 0800-000-000
            </p>
        </div>
    </body>
    </html>
    """

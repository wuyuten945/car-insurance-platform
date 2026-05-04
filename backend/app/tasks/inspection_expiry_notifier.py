"""
驗車到期通知排程

- 到期前 60 天：提醒
- 到期前 30 天：緊急（可開始驗車）
- 已逾期：逾期警告（逾期後 30 天內仍可驗車）

通知含：倒數天數、可驗車區間、強制險狀態（有效期需 >= 30 天）
通知管道：站內 + LINE + Email + SMS
每日 09:30 執行
"""
import logging
from datetime import date, timedelta, datetime, timezone

from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database import AsyncSessionLocal
from app.models.vehicle import UserVehicle
from app.models.user import User
from app.models.policy import Policy, PolicyItem
from app.models.notification import Notification
from app.core.sms import sms_gateway
from app.core.email import email_service
from app.core.line import line_service

logger = logging.getLogger(__name__)


async def check_inspection_expiry():
    """每日排程：檢查車輛驗車到期"""
    today = date.today()
    two_months_later = today + timedelta(days=60)

    logger.info(f"[排程] 檢查驗車到期通知 - {today}")
    print(f"\n[排程] 檢查驗車到期通知 - {today}")

    async with AsyncSessionLocal() as db:
        try:
            # 查詢到期前 60 天 ~ 逾期 30 天的車輛
            result = await db.execute(
                select(UserVehicle)
                .options(selectinload(UserVehicle.user))
                .where(
                    and_(
                        UserVehicle.registration_expiry.isnot(None),
                        UserVehicle.registration_expiry <= two_months_later,
                        UserVehicle.registration_expiry >= today - timedelta(days=30),
                    )
                )
            )
            vehicles = list(result.scalars().all())

            if not vehicles:
                print("   [OK] 目前沒有需要驗車通知的車輛")
                return

            for vehicle in vehicles:
                user = vehicle.user
                if not user:
                    continue

                days_left = (vehicle.registration_expiry - today).days

                # 檢查強制險（含到期日和剩餘天數）
                compulsory_info = await _check_compulsory_detail(db, user.id, vehicle.id, today)

                if days_left < -30:
                    continue  # 逾期超過 30 天不再通知
                elif days_left < 0:
                    level = "overdue"
                elif days_left <= 30:
                    level = "urgent"
                elif days_left <= 60:
                    level = "early"
                else:
                    continue

                await _send_inspection_notification(
                    db, user, vehicle, days_left, level, compulsory_info,
                    notification_key=f"inspection_{level}_{vehicle.id}_{vehicle.registration_expiry}",
                )

            await db.commit()
            print("   [OK] 驗車到期通知檢查完成\n")

        except Exception as e:
            await db.rollback()
            logger.error(f"[排程] 驗車到期通知失敗: {e}")
            print(f"   [ERROR] 驗車到期通知失敗: {e}\n")


async def _check_compulsory_detail(db: AsyncSession, user_id: str, vehicle_id: str, today: date) -> dict:
    """檢查強制險詳細狀態"""
    result = await db.execute(
        select(Policy)
        .options(selectinload(Policy.items))
        .where(
            and_(
                Policy.user_id == user_id,
                Policy.vehicle_id == vehicle_id,
                Policy.status.in_(["active", "expiring"]),
                Policy.end_date >= today,
            )
        )
    )
    best_expiry = None
    has_compulsory = False
    for policy in result.scalars().all():
        for item in policy.items:
            if "強制" in item.item_name and item.is_active:
                has_compulsory = True
                if best_expiry is None or policy.end_date > best_expiry:
                    best_expiry = policy.end_date

    days_remaining = (best_expiry - today).days if best_expiry else 0
    # 驗車時強制險有效期間必須 >= 30 天
    valid_for_inspection = has_compulsory and days_remaining >= 30

    return {
        "has_compulsory": has_compulsory,
        "expiry": best_expiry,
        "days_remaining": days_remaining,
        "valid_for_inspection": valid_for_inspection,
    }


async def _send_inspection_notification(
    db: AsyncSession,
    user: User,
    vehicle: UserVehicle,
    days_left: int,
    level: str,
    compulsory: dict,
    notification_key: str,
):
    """發送驗車到期通知（含倒數天數、可驗車區間、強制險狀態）"""
    # 查重
    existing = await db.execute(
        select(Notification).where(
            and_(
                Notification.user_id == user.id,
                Notification.notification_type == "inspection_reminder",
                Notification.body.contains(notification_key),
            )
        )
    )
    if existing.scalar_one_or_none():
        return

    user_name = user.name or "客戶"
    expiry_date = vehicle.registration_expiry
    expiry_str = expiry_date.strftime("%Y/%m/%d")
    plate = vehicle.plate_number
    car_desc = f"{vehicle.brand or ''} {vehicle.model or ''} ({plate})".strip()

    # 可驗車區間（到期前 30 天 ~ 到期後 30 天）
    inspect_start = (expiry_date - timedelta(days=30)).strftime("%Y/%m/%d")
    inspect_end = (expiry_date + timedelta(days=30)).strftime("%Y/%m/%d")
    window_info = f"可驗車區間：{inspect_start} ~ {inspect_end}"

    # 強制險狀態
    if compulsory["has_compulsory"]:
        comp_expiry_str = compulsory["expiry"].strftime("%Y/%m/%d") if compulsory["expiry"] else "未知"
        if compulsory["valid_for_inspection"]:
            compulsory_text = (
                f"[強制險] 有效，到期日 {comp_expiry_str}（剩餘 {compulsory['days_remaining']} 天），可辦理驗車。"
            )
        else:
            compulsory_text = (
                f"[強制險] 有效但剩餘僅 {compulsory['days_remaining']} 天（到期日 {comp_expiry_str}），"
                f"驗車需強制險有效期 >= 30 天，請先續保強制險再驗車。"
            )
    else:
        compulsory_text = "[強制險] 無有效強制汽車責任保險，依法無法辦理驗車。請先投保強制險。"

    # 倒數天數文字
    if days_left > 0:
        countdown = f"（倒數 {days_left} 天）"
    elif days_left == 0:
        countdown = "（今日到期）"
    else:
        countdown = f"（已逾期 {abs(days_left)} 天）"

    if level == "overdue":
        title = f"[逾期] {plate} 驗車已逾期 {abs(days_left)} 天"
        body = (
            f"{user_name} 您好，\n"
            f"您的 {car_desc} 行照已於 {expiry_str} 逾期{countdown}。\n"
            f"逾期驗車可能面臨罰鍰，請儘速辦理。\n\n"
            f"{window_info}\n"
            f"{compulsory_text}"
        )
        sms_msg = (
            f"[車險平台]{plate}行照逾期{abs(days_left)}天，"
            f"可驗車至{inspect_end}。"
        )
        if not compulsory["valid_for_inspection"]:
            sms_msg += " 強制險不足30天，請先續保。"
        email_subject = f"[逾期] {plate} 驗車逾期{countdown}"

    elif level == "urgent":
        title = f"[緊急] {plate} 驗車倒數 {days_left} 天"
        body = (
            f"{user_name} 您好，\n"
            f"您的 {car_desc} 行照將於 {expiry_str} 到期{countdown}。\n"
            f"已進入可驗車區間，請儘速安排。\n\n"
            f"{window_info}\n"
            f"{compulsory_text}"
        )
        sms_msg = (
            f"[車險平台]{plate}行照{days_left}天後到期，"
            f"已可驗車。"
        )
        if not compulsory["valid_for_inspection"]:
            sms_msg += " 強制險不足30天，請先續保。"
        email_subject = f"[緊急] {plate} 驗車倒數 {days_left} 天"

    else:  # early
        title = f"[提醒] {plate} 驗車倒數 {days_left} 天"
        body = (
            f"{user_name} 您好，\n"
            f"您的 {car_desc} 行照將於 {expiry_str} 到期{countdown}。\n"
            f"建議提早安排驗車。\n\n"
            f"{window_info}\n"
            f"{compulsory_text}"
        )
        sms_msg = f"[車險平台]{plate}行照{days_left}天後到期，建議提早驗車。"
        if not compulsory["valid_for_inspection"]:
            sms_msg += " 強制險不足30天，請先續保。"
        email_subject = f"[提醒] {plate} 驗車倒數 {days_left} 天"

    body_with_key = f"{body}\n<!-- {notification_key} -->"
    email_body = _build_inspection_email(user_name, vehicle, days_left, level, compulsory)

    # 發送通知
    db.add(Notification(
        user_id=user.id, title=title, body=body_with_key,
        notification_type="inspection_reminder",
        reference_type="vehicle", reference_id=vehicle.id, channel="multi",
    ))
    if user.phone:
        await sms_gateway.send(user.phone, sms_msg)
    if user.email:
        await email_service.send(user.email, email_subject, email_body)
    await line_service.send(user.id, f"{title}\n\n{body}")

    comp_status = "OK" if compulsory["valid_for_inspection"] else (
        f"不足({compulsory['days_remaining']}天)" if compulsory["has_compulsory"] else "無")
    print(f"   [NOTIFY][{level.upper()}] {plate} 到期{expiry_str}{countdown} 強制險:{comp_status}")


def _build_inspection_email(user_name: str, vehicle, days_left: int, level: str, compulsory: dict) -> str:
    from datetime import timedelta
    plate = vehicle.plate_number
    expiry_date = vehicle.registration_expiry
    expiry_str = expiry_date.strftime("%Y/%m/%d")
    color = "#D32F2F" if level in ("urgent", "overdue") else "#1565C0"
    car_desc = f"{vehicle.brand or ''} {vehicle.model or ''}"
    inspect_start = (expiry_date - timedelta(days=30)).strftime("%Y/%m/%d")
    inspect_end = (expiry_date + timedelta(days=30)).strftime("%Y/%m/%d")

    if compulsory["valid_for_inspection"]:
        comp_html = f'<td style="padding:8px;font-weight:bold;color:#2E7D32">有效（剩餘 {compulsory["days_remaining"]} 天）</td>'
    elif compulsory["has_compulsory"]:
        comp_html = f'<td style="padding:8px;font-weight:bold;color:#E65100">有效但不足 30 天（剩 {compulsory["days_remaining"]} 天），需先續保</td>'
    else:
        comp_html = '<td style="padding:8px;font-weight:bold;color:#D32F2F">未投保 - 無法驗車</td>'

    countdown = f"倒數 {days_left} 天" if days_left > 0 else (
        "今日到期" if days_left == 0 else f"已逾期 {abs(days_left)} 天")

    return f"""
    <html><body style="font-family:'Microsoft JhengHei',Arial,sans-serif;max-width:600px;margin:0 auto;">
    <div style="background:{color};color:white;padding:20px;border-radius:12px 12px 0 0;">
      <h2 style="margin:0">BOPINAN</h2>
      <p style="margin:8px 0 0">驗車到期通知 - {countdown}</p>
    </div>
    <div style="padding:24px;border:1px solid #e0e0e0;border-top:none;border-radius:0 0 12px 12px;">
      <p>{user_name} 您好，</p>
      <p>您的車輛驗車即將到期，請注意以下資訊：</p>
      <table style="width:100%;border-collapse:collapse;margin:16px 0;">
        <tr style="border-bottom:1px solid #eee"><td style="padding:8px;color:#666">車輛</td>
          <td style="padding:8px;font-weight:bold">{car_desc} ({plate})</td></tr>
        <tr style="border-bottom:1px solid #eee"><td style="padding:8px;color:#666">行照到期日</td>
          <td style="padding:8px;font-weight:bold;color:{color}">{expiry_str}</td></tr>
        <tr style="border-bottom:1px solid #eee"><td style="padding:8px;color:#666">倒數</td>
          <td style="padding:8px;font-weight:bold;color:{color}">{countdown}</td></tr>
        <tr style="border-bottom:1px solid #eee"><td style="padding:8px;color:#666">可驗車區間</td>
          <td style="padding:8px;font-weight:bold">{inspect_start} ~ {inspect_end}</td></tr>
        <tr><td style="padding:8px;color:#666">強制險</td>{comp_html}</tr>
      </table>
      {"<p style='color:#D32F2F;font-weight:bold'>強制險有效期不足 30 天，請先續保再驗車。</p>" if not compulsory["valid_for_inspection"] else ""}
      <a href="https://localhost:3000/inspection"
         style="display:inline-block;background:{color};color:white;padding:12px 24px;
                border-radius:8px;text-decoration:none;font-weight:bold;margin-top:8px">
        查詢附近驗車廠</a>
      <p style="color:#999;font-size:12px;margin-top:24px">
        此為系統自動發送，請勿直接回覆。<br>BOPINAN | 客服 0800-000-000</p>
    </div></body></html>"""

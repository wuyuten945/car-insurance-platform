"""
LINE Messaging API Webhook
- 收 LINE OA 事件（follow/unfollow/message）
- 驗證 HMAC-SHA256 簽章防止偽造請求
- 加好友時更新 User.is_line_friend = True，並發送歡迎訊息
- 取消好友時更新為 False
- 收到訊息時用 reply token 回覆（不耗推播配額）
"""
import base64
import hashlib
import hmac
import logging
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, Header, HTTPException, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.core.line_messaging import line_messaging
from app.dependencies import get_db
from app.models.user import User

logger = logging.getLogger(__name__)
router = APIRouter()


def _verify_signature(body: bytes, signature: str) -> bool:
    secret = (settings.LINE_MESSAGING_SECRET or "").encode("utf-8")
    if not secret:
        return False
    digest = hmac.new(secret, body, hashlib.sha256).digest()
    expected = base64.b64encode(digest).decode("utf-8")
    return hmac.compare_digest(expected, signature or "")


# LINE 內點連結會被內建瀏覽器卡住 → Google OAuth 會被拒絕。
# `?openExternalBrowser=1` 是 LINE 官方參數，會強制系統瀏覽器（Safari/Chrome）開啟。
PLATFORM_URL = "https://bopinan.ego-intl.com?openExternalBrowser=1"
LOGIN_URL = "https://bopinan.ego-intl.com/login?openExternalBrowser=1"

WELCOME_BOUND = (
    "👋 {name}，歡迎加入 BOPINAN 車險服務！\n\n"
    "您將收到以下個人化通知：\n"
    "🛡 理賠進度即時通知\n"
    "📅 續保 / 驗車到期提醒\n"
    "💬 業務員主動關懷\n\n"
    "有任何保單、理賠相關問題，可直接傳訊息給我們，業務員會盡快回覆。\n"
    f"也可至 {PLATFORM_URL} 查看完整服務。"
)

WELCOME_UNBOUND = (
    "👋 歡迎加入 BOPINAN！\n\n"
    "為了能收到您的個人化通知（理賠進度、續保提醒等），\n"
    f"請先到 {LOGIN_URL} 用 LINE 登入綁定帳號。\n\n"
    "綁定完成後就會自動收到通知。"
)

ACK_MESSAGE = (
    "感謝您的訊息，我們已收到。\n"
    "業務員將儘快與您聯繫。\n\n"
    f"若需查詢即時資訊，請至 {PLATFORM_URL}"
)


@router.post("/webhook")
async def line_webhook(
    request: Request,
    x_line_signature: str = Header(default=""),
    db: AsyncSession = Depends(get_db),
):
    body = await request.body()

    if not settings.LINE_MESSAGING_SECRET:
        logger.error("[LINE Webhook] LINE_MESSAGING_SECRET 未設定")
        raise HTTPException(status_code=500, detail="LINE webhook not configured")

    if not _verify_signature(body, x_line_signature):
        logger.warning("[LINE Webhook] 簽章驗證失敗")
        raise HTTPException(status_code=403, detail="Invalid signature")

    try:
        payload = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON")

    events = payload.get("events", []) or []
    for event in events:
        try:
            await _handle_event(event, db)
        except Exception as e:
            logger.error(f"[LINE Webhook] 事件處理失敗: {e}", exc_info=True)

    return {"ok": True}


async def _handle_event(event: dict, db: AsyncSession) -> None:
    event_type = event.get("type")
    line_user_id = (event.get("source") or {}).get("userId")
    if not line_user_id:
        return

    if event_type == "follow":
        await _on_follow(db, line_user_id)
    elif event_type == "unfollow":
        await _on_unfollow(db, line_user_id)
    elif event_type == "message":
        await _on_message(db, line_user_id, event)


async def _on_follow(db: AsyncSession, line_user_id: str) -> None:
    result = await db.execute(select(User).where(User.line_user_id == line_user_id))
    user = result.scalar_one_or_none()

    if user:
        user.is_line_friend = True
        user.line_friend_at = datetime.now(timezone.utc)
        await db.commit()
        logger.info(f"[LINE Webhook] {user.id} 加好友")
        await line_messaging.send_text(
            line_user_id,
            WELCOME_BOUND.format(name=user.name or "您好"),
        )
    else:
        await line_messaging.send_text(line_user_id, WELCOME_UNBOUND)


async def _on_unfollow(db: AsyncSession, line_user_id: str) -> None:
    result = await db.execute(select(User).where(User.line_user_id == line_user_id))
    user = result.scalar_one_or_none()
    if user:
        user.is_line_friend = False
        await db.commit()
        logger.info(f"[LINE Webhook] {user.id} 取消好友")


async def _on_message(db: AsyncSession, line_user_id: str, event: dict) -> None:
    message = event.get("message") or {}
    reply_token = event.get("replyToken")
    if not reply_token or message.get("type") != "text":
        return

    # Phase 1：簡單 ACK（Phase 3 再接 chatbot/客服轉接）
    await line_messaging.reply_text(reply_token, ACK_MESSAGE)

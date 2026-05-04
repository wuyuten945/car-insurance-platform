"""
LINE Messaging API 包裝
- send_text(line_user_id, text): 純文字推播
- send_template(line_user_id, alt_text, buttons): 帶按鈕的卡片
- broadcast_text(text): 廣播給全部好友（耗額度）

需要環境變數：
  LINE_MESSAGING_TOKEN  (Channel Access Token, long-lived)
"""
import logging
from typing import List, Optional, Dict, Any

import httpx

from app.config import settings

logger = logging.getLogger(__name__)

LINE_API = "https://api.line.me/v2/bot"


class LineMessagingService:
    def __init__(self):
        self.token = getattr(settings, "LINE_MESSAGING_TOKEN", "")

    def _headers(self) -> Dict[str, str]:
        return {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json",
        }

    async def send_text(self, line_user_id: str, text: str) -> bool:
        """推送純文字訊息給單一用戶"""
        if not self.token:
            logger.warning("[LINE] 未設定 LINE_MESSAGING_TOKEN，略過推播")
            return False
        if not line_user_id:
            logger.warning("[LINE] line_user_id 為空，略過推播")
            return False
        payload = {
            "to": line_user_id,
            "messages": [{"type": "text", "text": text[:5000]}],  # LINE 上限 5000 字
        }
        return await self._post(f"{LINE_API}/message/push", payload)

    async def send_buttons(
        self,
        line_user_id: str,
        title: str,
        text: str,
        buttons: List[Dict[str, str]],
        alt_text: str = "",
    ) -> bool:
        """
        發送帶按鈕的訊息（最多 4 個按鈕）。
        buttons 範例：[{"label": "查看保單", "uri": "https://..."}]
        """
        if not self.token or not line_user_id:
            return False
        actions = []
        for btn in buttons[:4]:
            if "uri" in btn:
                actions.append({"type": "uri", "label": btn["label"][:20], "uri": btn["uri"]})
            elif "data" in btn:
                actions.append({"type": "postback", "label": btn["label"][:20], "data": btn["data"]})
        payload = {
            "to": line_user_id,
            "messages": [{
                "type": "template",
                "altText": alt_text or title,
                "template": {
                    "type": "buttons",
                    "title": title[:40],
                    "text": text[:160],
                    "actions": actions,
                },
            }],
        }
        return await self._post(f"{LINE_API}/message/push", payload)

    async def broadcast_text(self, text: str) -> bool:
        """廣播給所有好友（每筆消耗額度，謹慎使用）"""
        if not self.token:
            return False
        payload = {"messages": [{"type": "text", "text": text[:5000]}]}
        return await self._post(f"{LINE_API}/message/broadcast", payload)

    async def reply_text(self, reply_token: str, text: str) -> bool:
        """用 reply token 回覆訊息（不耗 push 配額，需在 1 分鐘內使用）"""
        if not self.token or not reply_token:
            return False
        payload = {
            "replyToken": reply_token,
            "messages": [{"type": "text", "text": text[:5000]}],
        }
        return await self._post(f"{LINE_API}/message/reply", payload)

    async def get_quota(self) -> Optional[Dict[str, Any]]:
        """查詢推播額度餘額"""
        if not self.token:
            return None
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                r = await client.get(f"{LINE_API}/message/quota", headers=self._headers())
            if r.status_code == 200:
                return r.json()
        except Exception as e:
            logger.error(f"[LINE] quota 查詢失敗: {e}")
        return None

    async def _post(self, url: str, payload: dict) -> bool:
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                r = await client.post(url, headers=self._headers(), json=payload)
            if r.status_code in (200, 202):
                logger.info(f"[LINE] push 成功 → {payload.get('to', 'broadcast')[:12]}…")
                return True
            logger.error(f"[LINE] push 失敗 {r.status_code}: {r.text[:200]}")
            return False
        except Exception as e:
            logger.error(f"[LINE] push 例外: {e}")
            return False


line_messaging = LineMessagingService()


def can_push_to(user) -> bool:
    """三條件齊備才推播：line_user_id + is_line_friend + line_notify_enabled。"""
    return bool(
        user
        and user.line_user_id
        and getattr(user, "is_line_friend", False)
        and getattr(user, "line_notify_enabled", True)
    )


async def push_to_user(user, text: str) -> bool:
    """安全推播：條件不符靜默跳過，符合才推。"""
    if not can_push_to(user):
        return False
    return await line_messaging.send_text(user.line_user_id, text)

import re
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from app.models.chatbot import ChatbotSession, ChatbotMessage
from app.exceptions import NotFoundError


# 意圖辨識關鍵字映射
INTENT_KEYWORDS = {
    "policy_query": ["保單", "保險", "保額", "保費", "險種", "承保"],
    "renewal": ["續保", "到期", "續約", "比價", "報價"],
    "accident": ["車禍", "事故", "出事", "撞車", "碰撞", "緊急"],
    "claim": ["理賠", "賠償", "賠款", "進度", "立案", "申請理賠"],
    "account": ["帳號", "密碼", "資料", "修改", "信用卡", "個資"],
    "legal": ["法規", "法律", "罰款", "責任", "賠償", "強制險", "酒駕"],
    "general": ["你好", "謝謝", "客服", "人工", "幫助", "問題"],
}

# 預設回覆
INTENT_RESPONSES = {
    "policy_query": "關於保單查詢，您可以在「保單管理」頁面查看所有保單資訊，包括承保項目、保額、保費明細和不賠事項。請問您想查詢哪方面的保單資訊？",
    "renewal": "關於續保，您可以在「續保比較」頁面查看多家保險公司的報價比較。系統會在保單到期前 60 天開始提醒您。請問您的保單何時到期？",
    "accident": "如果您現在發生事故，請立即點擊首頁的 SOS 緊急按鈕，系統會自動定位並提供完整的處理流程引導。需要我為您啟動緊急處理模式嗎？",
    "claim": "關於理賠，您可以在「理賠追蹤」頁面查看所有理賠案件的進度。如需申請新的理賠，請點擊「申請理賠」按鈕。請問您是要查詢現有理賠進度，還是申請新的理賠？",
    "account": "關於帳戶管理，您可以在「個人資料」頁面修改基本資料、管理車輛資訊和信用卡。請問您需要修改哪項資料？",
    "legal": "關於法規查詢，您可以在「法規查詢」功能中搜尋交通法規、保險法規等。請問您想了解哪方面的法律問題？\n\n⚠️ 提醒：本平台無法提供法律建議，如有法律疑問建議諮詢專業律師。",
    "general": "您好！我是車險智能服務平台的客服助手。我可以協助您：\n\n1. 查詢保單資訊\n2. 續保比較\n3. 車禍緊急處理\n4. 理賠進度查詢\n5. 帳戶管理\n6. 法規查詢\n\n請問有什麼可以幫您的？",
}

FALLBACK_RESPONSE = "抱歉，我不太理解您的問題。我可以協助您處理保單查詢、續保、車禍處理、理賠、帳戶管理和法規查詢等問題。您也可以輸入「轉人工」與真人客服對話。"
TRANSFER_RESPONSE = "好的，正在為您轉接人工客服，請稍候..."


class ChatbotService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_session(self, user_id: str) -> ChatbotSession:
        session = ChatbotSession(user_id=user_id)
        self.db.add(session)
        await self.db.flush()

        # 歡迎訊息
        welcome = ChatbotMessage(
            session_id=session.id,
            sender="bot",
            content=INTENT_RESPONSES["general"],
            intent="general",
            confidence=1.0,
        )
        self.db.add(welcome)
        await self.db.flush()
        return session

    async def send_message(self, session_id: str, content: str) -> list[ChatbotMessage]:
        # 儲存使用者訊息
        user_msg = ChatbotMessage(
            session_id=session_id,
            sender="user",
            content=content,
        )
        self.db.add(user_msg)

        # 檢查是否要轉人工
        if any(kw in content for kw in ["轉人工", "真人客服", "人工客服"]):
            bot_msg = ChatbotMessage(
                session_id=session_id,
                sender="bot",
                content=TRANSFER_RESPONSE,
                intent="transfer_human",
                confidence=1.0,
            )
            self.db.add(bot_msg)
            # 更新 session 狀態
            result = await self.db.execute(
                select(ChatbotSession).where(ChatbotSession.id == session_id)
            )
            session = result.scalar_one_or_none()
            if session:
                session.status = "transferred_to_human"
            await self.db.flush()
            return [user_msg, bot_msg]

        # 意圖辨識
        intent, confidence = self._detect_intent(content)
        user_msg.intent = intent
        user_msg.confidence = confidence

        # 生成回覆
        if confidence >= 0.5:
            response_text = INTENT_RESPONSES.get(intent, FALLBACK_RESPONSE)
        else:
            response_text = FALLBACK_RESPONSE

        bot_msg = ChatbotMessage(
            session_id=session_id,
            sender="bot",
            content=response_text,
            intent=intent,
            confidence=confidence,
        )
        self.db.add(bot_msg)
        await self.db.flush()
        return [user_msg, bot_msg]

    def _detect_intent(self, text: str) -> tuple[str, float]:
        """簡易關鍵字意圖辨識（生產環境替換為 NLU 模型）"""
        scores = {}
        for intent, keywords in INTENT_KEYWORDS.items():
            score = sum(1 for kw in keywords if kw in text)
            if score > 0:
                scores[intent] = score

        if not scores:
            return "unknown", 0.0

        best_intent = max(scores, key=scores.get)
        max_possible = len(INTENT_KEYWORDS[best_intent])
        confidence = min(scores[best_intent] / max(max_possible * 0.3, 1), 1.0)
        return best_intent, round(confidence, 2)

    async def get_session(self, session_id: str) -> ChatbotSession:
        result = await self.db.execute(
            select(ChatbotSession).options(
                selectinload(ChatbotSession.messages)
            ).where(ChatbotSession.id == session_id)
        )
        session = result.scalar_one_or_none()
        if not session:
            raise NotFoundError("客服對話不存在")
        return session

    async def end_session(self, session_id: str, rating: int = None) -> None:
        result = await self.db.execute(
            select(ChatbotSession).where(ChatbotSession.id == session_id)
        )
        session = result.scalar_one_or_none()
        if session:
            session.status = "closed"
            session.ended_at = datetime.now(timezone.utc)
            if rating:
                session.satisfaction_rating = rating

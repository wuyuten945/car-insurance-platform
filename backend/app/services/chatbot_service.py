import re
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from app.models.chatbot import ChatbotSession, ChatbotMessage
from app.exceptions import NotFoundError


# ──────────────────────────────────────────────────────────────
# 服務導引（FAQ）— 此模組以「指向功能位置」為主，不嘗試解答個案。
# 個案、保單細節、法律建議請走「轉人工」交由真人客服處理。
# ──────────────────────────────────────────────────────────────

# 意圖辨識關鍵字映射（涵蓋前台所有服務）
INTENT_KEYWORDS = {
    "policy_query":    ["保單", "保險", "保額", "保費", "險種", "承保", "保單號"],
    "renewal":         ["續保", "到期", "續約", "比價", "報價", "詢價工單", "詢價"],
    "quote_estimate":  ["試算", "簡易試算", "保費試算", "預估保費"],
    "accident":        ["車禍", "事故", "出事", "撞車", "碰撞", "緊急", "SOS", "sos"],
    "claim":           ["理賠", "賠償", "賠款", "進度", "立案", "申請理賠", "理賠進度"],
    "vehicle":         ["車輛", "行照", "車主", "車籍", "車牌", "新增車", "管理車"],
    "license":         ["駕照", "駕駛執照"],
    "inspection":      ["驗車", "定檢", "檢驗", "監理"],
    "account":         ["帳號", "密碼", "個人資料", "修改資料", "信用卡", "個資", "通知"],
    "legal":           ["法規", "法律", "罰款", "罰則", "強制險法規", "酒駕"],
    "numerology":      ["數字易經", "拿副好牌", "磁場", "吉星", "凶星"],
    "transfer":        ["轉人工", "真人", "人工客服", "找業務員", "找專員"],
    "general":         ["你好", "您好", "謝謝", "幫助", "什麼", "怎麼用"],
}

# 服務導引回覆 — 統一語氣：先告訴位置 / 再提示注意事項 / 最後給轉人工出口
INTENT_RESPONSES = {
    "policy_query":
        "📋 保單查詢\n"
        "「我的保單」或下方分頁切到保單管理，可看到所有保單清單（強制險 + 任意險）。\n"
        "點任一張保單可看：承保項目、保額、保費、不賠事項、保單期間。\n\n"
        "📝 個案問題（保單條款細節、理算邏輯）→ 請輸入「轉人工」由業務員回覆。",
    "renewal":
        "🔄 續保 / 詢價\n"
        "・自助比價試算：「保費簡易試算(參考)」可立即看預估金額\n"
        "・正式報價：「我的車險續期保費詢價」→「新增詢價」→ 自動派給您的業務員或管理員,6-12 小時內回覆。\n"
        "・系統會在保單到期前 60 天開始提醒。",
    "quote_estimate":
        "💰 保費簡易試算\n"
        "「保費簡易試算(參考)」頁面填車輛資訊與想保項目,系統會立即估算金額。\n"
        "⚠️ 提醒：試算結果僅供參考,正式金額以保險公司核保為準。需要正式報價請按下方「請業務員精確報價」。",
    "accident":
        "🚨 車禍/事故處理\n"
        "立即操作：首頁 SOS 緊急按鈕 → 系統會自動定位、提供處理流程、可直接撥 110/119。\n"
        "若已脫離立即危險,請保留現場照片並到「申請理賠」上傳。\n\n"
        "需要真人協助請輸入「轉人工」。",
    "claim":
        "📑 理賠服務\n"
        "・查進度：「理賠服務」→「理賠追蹤」可看每個案件的處理階段\n"
        "・新申請：「理賠服務」→「申請理賠」上傳照片、警方紀錄、維修估價單\n"
        "・無法走理賠的保單（自填非業務員建立）會在卡片上顯示鎖頭,請聯繫業務員處理。",
    "vehicle":
        "🚗 車輛 / 行照管理\n"
        "「我的」→「車輛管理」可新增/編輯車輛、上傳行照,系統會自動提醒驗車到期。\n"
        "車主資料若不一致會影響理賠,請務必和保單的被保險人對齊。",
    "license":
        "🪪 駕照管理\n"
        "「我的」→「駕照管理」上傳駕照正反面,系統會自動提醒換照到期日。",
    "inspection":
        "🔍 驗車查詢\n"
        "首頁的「驗車查詢」可輸入車牌查詢應驗日期。\n"
        "您車輛在系統內的話,「車輛管理」會自動帶出最近一次驗車狀態。",
    "account":
        "⚙️ 帳戶與通知設定\n"
        "「我的」→「個人資料」可修改：姓名、電話、Email、密碼、信用卡、通知方式（Email/LINE 推播）、提醒天數。\n"
        "頭像點兩下進入帳號安全頁可查看登入紀錄。",
    "legal":
        "📚 法規查詢\n"
        "「法規查詢」可查交通法規、保險法規、強制險條款。\n\n"
        "⚠️ 重要：本平台僅提供法規條文查詢,不提供法律建議。涉及具體案件、賠償談判、訴訟事宜請諮詢專業律師。",
    "numerology":
        "✨ 數字易經（幫人生拿副好牌）\n"
        "「我的」→「幫人生拿副好牌」可分析身分證、生日、電話、車牌的八磁場吉凶,並產生避凶補吉的建議號碼。\n"
        "本系統僅供參考,不構成任何決策依據。",
    "transfer":
        "正在為您轉接專人客服,請稍候。業務員/客服收到通知後會主動聯繫您。\n"
        "若您有指定業務員,系統會優先派給該業務員;若無業務員則交由管理員處理。",
    "general":
        "您好！這裡是 BOPINAN 服務導引中心 📖\n\n"
        "可協助指引以下服務：\n"
        "1. 📋 保單查詢與管理\n"
        "2. 🔄 續保比價、詢價工單\n"
        "3. 💰 保費簡易試算\n"
        "4. 🚨 車禍 / SOS 緊急處理\n"
        "5. 📑 理賠申請與進度查詢\n"
        "6. 🚗 車輛 / 行照 / 駕照管理\n"
        "7. 🔍 驗車查詢\n"
        "8. ⚙️ 帳戶與通知設定\n"
        "9. 📚 交通 / 保險法規查詢\n"
        "10. ✨ 數字易經（幫人生拿副好牌）\n\n"
        "請輸入關鍵字（如「保單」「理賠」「續保」「SOS」）找指引,或下方按鈕快速進入。\n"
        "需要真人協助請輸入「轉人工」。",
}

FALLBACK_RESPONSE = (
    "🔍 找不到對應的服務指引。\n"
    "您可以試試這些關鍵字：保單、續保、試算、SOS、理賠、車輛、行照、駕照、驗車、帳戶、法規、數字易經\n\n"
    "若是個案問題（保單細節、理賠談判、法律疑問）建議直接輸入「轉人工」由真人協助。"
)
TRANSFER_RESPONSE = INTENT_RESPONSES["transfer"]


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

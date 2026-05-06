import logging
import random
import string
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

from fastapi import UploadFile
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.line_messaging import line_messaging
from app.core.storage import storage
from app.exceptions import BadRequestError, NotFoundError
from app.models.claim import Claim, ClaimAdjuster, ClaimDocument, ClaimProgress
from app.models.user import User
from app.schemas.claim import ClaimCreate

logger = logging.getLogger(__name__)
TPE_TZ = ZoneInfo("Asia/Taipei")


CLAIM_STAGES = [
    "submitted",      # 立案確認
    "reviewing",      # 文件審核
    "investigating",  # 現場勘查
    "negotiating",    # 責任認定
    "approved",       # 理賠金額確認
    "paying",         # 撥款作業
    "closed",         # 案件結案
]

STAGE_LABELS = {
    "submitted": "立案確認",
    "reviewing": "文件審核",
    "investigating": "現場勘查",
    "negotiating": "責任認定",
    "approved": "理賠金額確認",
    "paying": "撥款作業",
    "closed": "案件結案",
}

STAGE_EMOJI = {
    "submitted": "📝",
    "reviewing": "📋",
    "investigating": "🔍",
    "negotiating": "⚖️",
    "approved": "✅",
    "paying": "💰",
    "closed": "🎉",
}


def generate_claim_number() -> str:
    prefix = datetime.now().strftime("%Y%m%d")
    suffix = "".join(random.choices(string.digits, k=6))
    return f"CLM-{prefix}-{suffix}"


class ClaimService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_claim(self, user_id: str, data: ClaimCreate) -> Claim:
        # 先驗證 policy 屬於這位使用者（避免 FK 失敗 → 500）
        from app.models.policy import Policy
        pol = await self.db.execute(
            select(Policy).where(Policy.id == data.policy_id, Policy.user_id == user_id)
        )
        if not pol.scalar_one_or_none():
            raise BadRequestError("找不到此保單，或該保單不屬於您")

        # 前台金額用 amount_claimed，後端欄位是 claimed_amount → 兩個都接，前者優先
        amount = data.claimed_amount if data.claimed_amount is not None else data.amount_claimed

        # 把前台表單其他欄位（事故描述等）合進 notes
        notes_parts = []
        if data.notes:
            notes_parts.append(str(data.notes))
        if data.description:
            notes_parts.append(f"【事故描述】{data.description}")
        if data.location:
            notes_parts.append(f"【事故地點】{data.location}")
        if data.occurred_at:
            notes_parts.append(f"【事故時間】{data.occurred_at.isoformat()}")
        if data.accident_type:
            notes_parts.append(f"【事故類型】{data.accident_type}")
        if data.my_situation:
            notes_parts.append(f"【行車狀態】{data.my_situation}")
        merged_notes = "\n".join(notes_parts) if notes_parts else None

        claim = Claim(
            user_id=user_id,
            accident_id=data.accident_id,
            policy_id=data.policy_id,
            claim_number=generate_claim_number(),
            claim_type=data.claim_type,
            claimed_amount=amount,
            notes=merged_notes,
        )
        self.db.add(claim)
        await self.db.flush()

        # 初始進度記錄
        progress = ClaimProgress(
            claim_id=claim.id,
            stage="submitted",
            description="系統已收到理賠申請，案件已建立。",
            changed_by="system",
        )
        self.db.add(progress)

        # 自動分配理賠專員（Mock）
        adjuster = ClaimAdjuster(
            claim_id=claim.id,
            adjuster_name="王小明",
            adjuster_phone="02-27001234 分機 567",
            adjuster_email="wang.xiaoming@insurance.com.tw",
            service_hours="週一至週五 09:00-18:00",
            backup_phone="0800-000-888",
            avg_response_minutes=45,
        )
        self.db.add(adjuster)
        await self.db.flush()

        # 重新撈一次 claim 把關聯（progress / adjuster / documents）一併載進來
        # 否則 ClaimOut.model_validate(claim) 會觸發 async lazy-load → MissingGreenlet → 500
        loaded = await self.db.execute(
            select(Claim).options(
                selectinload(Claim.progress_history),
                selectinload(Claim.adjuster),
                selectinload(Claim.documents),
            ).where(Claim.id == claim.id)
        )
        return loaded.scalar_one()

    async def list_claims(self, user_id: str, status: str = None) -> list[Claim]:
        query = select(Claim).options(
            selectinload(Claim.progress_history),
            selectinload(Claim.adjuster),
            selectinload(Claim.documents),
        ).where(Claim.user_id == user_id)

        if status:
            query = query.where(Claim.status == status)
        query = query.order_by(Claim.submitted_at.desc())

        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def get_claim(self, user_id: str, claim_id: str) -> Claim:
        result = await self.db.execute(
            select(Claim).options(
                selectinload(Claim.progress_history),
                selectinload(Claim.adjuster),
                selectinload(Claim.documents),
            ).where(Claim.id == claim_id, Claim.user_id == user_id)
        )
        claim = result.scalar_one_or_none()
        if not claim:
            raise NotFoundError("理賠案件不存在")
        return claim

    async def get_claim_progress(self, claim_id: str) -> list[ClaimProgress]:
        result = await self.db.execute(
            select(ClaimProgress).where(ClaimProgress.claim_id == claim_id)
            .order_by(ClaimProgress.changed_at)
        )
        return list(result.scalars().all())

    async def upload_document(
        self, claim_id: str, file: UploadFile, document_type: str
    ) -> ClaimDocument:
        file_url = await storage.upload(file, subfolder=f"claims/{claim_id}")
        doc = ClaimDocument(
            claim_id=claim_id,
            document_type=document_type,
            file_url=file_url,
            file_name=file.filename,
            file_size_bytes=file.size if file.size else 0,
        )
        self.db.add(doc)
        await self.db.flush()
        return doc

    async def update_progress(
        self,
        claim_id: str,
        new_stage: str,
        description: str,
        changed_by: str = "system",
    ) -> Claim:
        """
        更新理賠案件進度：寫 Claim.status + 新增 ClaimProgress 紀錄。
        **不**做 LINE 推播 — 由呼叫端 commit 成功後另外呼叫 notify_progress()，
        避免 commit 失敗仍發出幽靈通知。
        """
        if new_stage not in CLAIM_STAGES:
            raise BadRequestError(f"無效的進度階段：{new_stage}")

        result = await self.db.execute(
            select(Claim).options(selectinload(Claim.adjuster)).where(Claim.id == claim_id)
        )
        claim = result.scalar_one_or_none()
        if not claim:
            raise NotFoundError("理賠案件不存在")

        claim.status = new_stage
        if new_stage == "closed":
            claim.resolved_at = datetime.now(timezone.utc)

        progress = ClaimProgress(
            claim_id=claim.id,
            stage=new_stage,
            description=description,
            changed_by=changed_by,
        )
        self.db.add(progress)
        await self.db.flush()
        return claim

    async def notify_progress(self, claim: Claim, stage: str, description: str) -> None:
        """commit 後呼叫，做 LINE 推播。失敗只記 log 不拋例外。"""
        await self._notify_line(claim, stage, description)

    async def _notify_line(self, claim: Claim, stage: str, description: str) -> None:
        """檢查用戶 LINE 通知意願，符合條件才推播。失敗不拋例外。"""
        try:
            user_res = await self.db.execute(select(User).where(User.id == claim.user_id))
            user = user_res.scalar_one_or_none()
            if not user:
                return
            if not user.line_user_id:
                logger.info(f"[Claim Notify] {claim.claim_number} 用戶未綁定 LINE，略過")
                return
            if not user.is_line_friend:
                logger.info(f"[Claim Notify] {claim.claim_number} 用戶未加 OA 好友，略過")
                return
            if not user.line_notify_enabled:
                logger.info(f"[Claim Notify] {claim.claim_number} 用戶關閉通知，略過")
                return

            now_tpe = datetime.now(TPE_TZ).strftime("%m/%d %H:%M")
            label = STAGE_LABELS.get(stage, stage)
            emoji = STAGE_EMOJI.get(stage, "🛡")
            adjuster_line = ""
            if claim.adjuster and claim.adjuster.adjuster_name:
                adjuster_line = f"\n專員：{claim.adjuster.adjuster_name}"

            msg = (
                f"🛡 BOPINAN 理賠進度更新\n\n"
                f"案件編號：{claim.claim_number}\n"
                f"最新狀態：{emoji} {label}\n"
                f"時間：{now_tpe}{adjuster_line}\n\n"
                f"📝 {description}\n\n"
                f"查看完整進度：\n"
                f"https://bopinan.ego-intl.com/claims/{claim.id}?openExternalBrowser=1"
            )

            sent = await line_messaging.send_text(user.line_user_id, msg)
            if sent:
                logger.info(f"[Claim Notify] {claim.claim_number} 推播成功 → {user.id}")
            else:
                logger.warning(f"[Claim Notify] {claim.claim_number} 推播失敗 → {user.id}")
        except Exception as e:
            logger.error(f"[Claim Notify] {claim.claim_number} 推播例外: {e}", exc_info=True)

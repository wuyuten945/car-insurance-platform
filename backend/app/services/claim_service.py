from datetime import datetime, timezone
import random
import string
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from fastapi import UploadFile
from app.models.claim import Claim, ClaimDocument, ClaimProgress, ClaimAdjuster
from app.schemas.claim import ClaimCreate
from app.core.storage import storage
from app.exceptions import NotFoundError


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


def generate_claim_number() -> str:
    prefix = datetime.now().strftime("%Y%m%d")
    suffix = "".join(random.choices(string.digits, k=6))
    return f"CLM-{prefix}-{suffix}"


class ClaimService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_claim(self, user_id: str, data: ClaimCreate) -> Claim:
        claim = Claim(
            user_id=user_id,
            accident_id=data.accident_id,
            policy_id=data.policy_id,
            claim_number=generate_claim_number(),
            claim_type=data.claim_type,
            claimed_amount=data.claimed_amount,
            notes=data.notes,
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
        return claim

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

from pydantic import BaseModel
from datetime import datetime
from decimal import Decimal


class ClaimCreate(BaseModel):
    accident_id: str | None = None
    policy_id: str
    claim_type: str | None = None
    claimed_amount: Decimal | None = None
    notes: str | None = None


class ClaimProgressOut(BaseModel):
    id: str
    stage: str
    description: str | None = None
    changed_by: str | None = None
    changed_at: datetime

    model_config = {"from_attributes": True}


class ClaimAdjusterOut(BaseModel):
    adjuster_name: str
    adjuster_phone: str | None = None
    adjuster_email: str | None = None
    service_hours: str | None = None
    backup_phone: str | None = None
    avg_response_minutes: int | None = None

    model_config = {"from_attributes": True}


class ClaimDocumentOut(BaseModel):
    id: str
    document_type: str
    file_url: str
    file_name: str | None = None
    uploaded_at: datetime | None = None

    model_config = {"from_attributes": True}


class ClaimOut(BaseModel):
    id: str
    claim_number: str
    status: str
    claim_type: str | None = None
    claimed_amount: Decimal | None = None
    approved_amount: Decimal | None = None
    submitted_at: datetime
    resolved_at: datetime | None = None
    notes: str | None = None
    progress_history: list[ClaimProgressOut] = []
    adjuster: ClaimAdjusterOut | None = None
    documents: list[ClaimDocumentOut] = []
    created_at: datetime

    model_config = {"from_attributes": True}

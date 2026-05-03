from sqlalchemy import Column, String, Boolean, DateTime, Numeric, Text, ForeignKey, Integer, Index
from sqlalchemy.orm import relationship
from app.database import Base, TimestampMixin, generate_uuid
from datetime import datetime, timezone


class Claim(TimestampMixin, Base):
    __tablename__ = "claims"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    accident_id = Column(String(36), ForeignKey("accidents.id"))
    policy_id = Column(String(36), ForeignKey("policies.id"), nullable=False)
    claim_number = Column(String(50), unique=True, nullable=False)
    status = Column(String(30), nullable=False, default="submitted")
    # 7 stages: submitted, reviewing, investigating, negotiating, approved, paying, closed
    claim_type = Column(String(30))  # own_damage, third_party, medical, comprehensive
    claimed_amount = Column(Numeric(14, 2))
    approved_amount = Column(Numeric(14, 2))
    submitted_at = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))
    resolved_at = Column(DateTime)
    notes = Column(Text)

    user = relationship("User", back_populates="claims")
    documents = relationship("ClaimDocument", back_populates="claim", lazy="selectin")
    progress_history = relationship("ClaimProgress", back_populates="claim", lazy="selectin", order_by="ClaimProgress.changed_at")
    adjuster = relationship("ClaimAdjuster", back_populates="claim", uselist=False, lazy="selectin")

    __table_args__ = (
        Index("ix_claims_user_status", "user_id", "status"),
    )


class ClaimDocument(TimestampMixin, Base):
    __tablename__ = "claim_documents"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    claim_id = Column(String(36), ForeignKey("claims.id"), nullable=False, index=True)
    document_type = Column(String(50), nullable=False)
    # accident_photos, driving_license, vehicle_license, police_report, scene_diagram,
    # medical_certificate, medical_receipt, repair_estimate, bank_info, affidavit, settlement
    file_url = Column(String(500), nullable=False)
    file_name = Column(String(255))
    file_size_bytes = Column(Integer)
    uploaded_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    claim = relationship("Claim", back_populates="documents")


class ClaimProgress(TimestampMixin, Base):
    __tablename__ = "claim_progress"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    claim_id = Column(String(36), ForeignKey("claims.id"), nullable=False)
    stage = Column(String(30), nullable=False)
    description = Column(Text)
    changed_by = Column(String(100))  # adjuster name or 'system'
    changed_at = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))

    claim = relationship("Claim", back_populates="progress_history")

    __table_args__ = (
        Index("ix_claim_progress_claim_date", "claim_id", "changed_at"),
    )


class ClaimAdjuster(TimestampMixin, Base):
    __tablename__ = "claim_adjusters"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    claim_id = Column(String(36), ForeignKey("claims.id"), nullable=False, unique=True)
    adjuster_name = Column(String(100), nullable=False)
    adjuster_phone = Column(String(20))
    adjuster_email = Column(String(255))
    service_hours = Column(String(100))
    backup_phone = Column(String(20))  # 0800 主線
    avg_response_minutes = Column(Integer)  # 過去30天平均回覆時間
    assigned_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    is_active = Column(Boolean, default=True)

    claim = relationship("Claim", back_populates="adjuster")

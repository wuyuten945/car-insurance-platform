"""詢價工單 — 客戶送出 → 業務員/管理員實際向產險公司詢價 → 多家報價匯整回客戶"""
from sqlalchemy import (
    Column, String, Boolean, Integer, Date, DateTime, ForeignKey, Numeric, Text, Index, JSON,
)
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from app.database import Base, TimestampMixin, generate_uuid


class QuoteRequest(TimestampMixin, Base):
    __tablename__ = "quote_requests"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False, index=True)
    vehicle_id = Column(String(36), ForeignKey("user_vehicles.id"), nullable=True)
    source_policy_id = Column(String(36), ForeignKey("policies.id"), nullable=True)

    # 詢價內容
    use_existing_policy = Column(Boolean, default=False)        # 「跟原保單一樣」（基於 source_policy_id）
    desired_items = Column(JSON)                                 # [{name, limit?, note?}, ...]
    driver_age = Column(Integer)                                 # 駕駛人年齡（影響費率）
    claims_count_3y = Column(Integer)                            # 過去 3 年出險次數（自填）
    surcharge_pct = Column(Numeric(5, 2))                        # 客戶自知的加費%（如 +20.00）
    notes = Column(Text)                                         # 客戶備註 / 特別需求

    # 指派
    assigned_to_admin_id = Column(String(36), ForeignKey("admin_users.id"), nullable=True, index=True)

    # 狀態：pending（待處理）/ in_progress（業務員處理中）/ quoted（已回報）/ completed（已成交或結案）/ cancelled
    status = Column(String(20), nullable=False, default="pending", index=True)
    submitted_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    quoted_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)

    user = relationship("User")
    vehicle = relationship("UserVehicle")
    source_policy = relationship("Policy")
    assigned_admin = relationship("AdminUser")
    responses = relationship("QuoteResponse", back_populates="request", lazy="selectin", cascade="all, delete-orphan")

    __table_args__ = (
        Index("ix_quote_req_user_status", "user_id", "status"),
    )


class QuoteResponse(TimestampMixin, Base):
    """單張保單的回報報價（一張詢價工單可有多個 response）"""
    __tablename__ = "quote_responses"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    quote_request_id = Column(String(36), ForeignKey("quote_requests.id"), nullable=False, index=True)
    insurer_name = Column(String(100), nullable=False)
    quoted_premium = Column(Numeric(12, 2), nullable=False)
    coverage_details = Column(JSON)             # [{name, limit?, premium?}, ...]
    valid_until = Column(Date)
    notes = Column(Text)
    is_recommended = Column(Boolean, default=False)

    request = relationship("QuoteRequest", back_populates="responses")

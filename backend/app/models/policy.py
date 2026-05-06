from sqlalchemy import Column, String, Boolean, Date, DateTime, Time, Numeric, Text, ForeignKey, Index, JSON
from sqlalchemy.orm import relationship
from app.database import Base, TimestampMixin, generate_uuid


class Policy(TimestampMixin, Base):
    __tablename__ = "policies"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    vehicle_id = Column(String(36), ForeignKey("user_vehicles.id"))
    insurer_name = Column(String(100), nullable=False)
    policy_number = Column(String(50), unique=True, nullable=False)
    status = Column(String(20), nullable=False, default="active")  # active, expiring, expired, cancelled
    # 任意險 期間（一般車險：綜合險 / 第三人 / 車損 等）
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    # 起保 / 到期 的「時:分」精度（NULL = 整日，舊資料保留 NULL）
    start_time = Column(Time, nullable=True)
    end_time = Column(Time, nullable=True)
    # 強制險 全套（汽車強制責任險）— 可能跟任意險不同保險公司、不同保單號、不同保費、不同期間
    # 舊資料/未填皆為 NULL；要保人自己若只有強制險而無任意險，仍以上方欄位為主
    compulsory_insurer_name = Column(String(100), nullable=True)
    compulsory_policy_number = Column(String(50), nullable=True)
    compulsory_premium = Column(Numeric(12, 2), nullable=True)
    compulsory_start_date = Column(Date, nullable=True)
    compulsory_end_date = Column(Date, nullable=True)
    compulsory_start_time = Column(Time, nullable=True)
    compulsory_end_time = Column(Time, nullable=True)
    total_premium = Column(Numeric(12, 2))
    document_url = Column(String(500))

    user = relationship("User", back_populates="policies")
    vehicle = relationship("UserVehicle", back_populates="policies")
    items = relationship("PolicyItem", back_populates="policy", lazy="selectin")
    payments = relationship("PremiumPayment", back_populates="policy", lazy="noload")
    renewal_quotes = relationship("RenewalQuote", back_populates="policy", lazy="noload")

    __table_args__ = (
        Index("ix_policies_user_status", "user_id", "status"),
        Index("ix_policies_end_date", "end_date"),
    )


class PolicyItem(TimestampMixin, Base):
    __tablename__ = "policy_items"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    policy_id = Column(String(36), ForeignKey("policies.id"), nullable=False, index=True)
    item_name = Column(String(100), nullable=False)  # 強制責任險, 車體損失險, 第三人責任險, 竊盜險, 超額責任險
    coverage_limit = Column(Numeric(14, 2))
    deductible = Column(Numeric(10, 2))
    premium = Column(Numeric(10, 2))
    is_active = Column(Boolean, default=True)
    description = Column(Text)
    exclusions = Column(Text)  # 不賠事項，以 JSON 字串存放

    policy = relationship("Policy", back_populates="items")


class PremiumPayment(TimestampMixin, Base):
    __tablename__ = "premium_payments"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    policy_id = Column(String(36), ForeignKey("policies.id"), nullable=False, index=True)
    payment_method_id = Column(String(36), ForeignKey("payment_methods.id"))
    amount = Column(Numeric(12, 2), nullable=False)
    due_date = Column(Date)
    paid_date = Column(Date)
    status = Column(String(20), default="pending")  # pending, paid, overdue, failed
    transaction_ref = Column(String(100))

    policy = relationship("Policy", back_populates="payments")
    payment_method = relationship("PaymentMethod")


class PaymentMethod(TimestampMixin, Base):
    __tablename__ = "payment_methods"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False, index=True)
    method_type = Column(String(30), nullable=False)  # credit_card, bank_transfer, convenience_store
    card_brand = Column(String(20))  # visa, mastercard, jcb
    last_four = Column(String(4))
    bank_name = Column(String(50))
    is_default = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)


class RenewalQuote(TimestampMixin, Base):
    __tablename__ = "renewal_quotes"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    policy_id = Column(String(36), ForeignKey("policies.id"), nullable=False, index=True)
    insurer_name = Column(String(100), nullable=False)
    insurer_logo_url = Column(String(500))
    quoted_premium = Column(Numeric(12, 2), nullable=False)
    coverage_details = Column(JSON)
    rating = Column(Numeric(2, 1))  # 客戶評分 1.0-5.0
    claim_speed_days = Column(Numeric(4, 1))  # 平均理賠天數
    features = Column(Text)  # 特色說明
    valid_until = Column(Date)
    is_selected = Column(Boolean, default=False)

    policy = relationship("Policy", back_populates="renewal_quotes")

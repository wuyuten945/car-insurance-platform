from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, Index
from sqlalchemy.orm import relationship
from app.database import Base, TimestampMixin, generate_uuid


class User(TimestampMixin, Base):
    __tablename__ = "users"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    # phone 可為 NULL：OAuth/Email 註冊不一定有手機。NULL 不算 unique 衝突，
    # 同一手機號碼仍不允許多帳號。
    phone = Column(String(20), unique=True, nullable=True, index=True)
    name = Column(String(100))
    email = Column(String(255), unique=True, index=True)
    id_number_hash = Column(String(255))
    birth_date = Column(DateTime(timezone=True))
    address = Column(String(500))
    registered_address = Column(String(500))
    emergency_contact_name = Column(String(100))
    emergency_contact_phone = Column(String(20))
    emergency_contact_relation = Column(String(50))
    license_number = Column(String(50))
    license_expiry = Column(DateTime(timezone=True))
    avatar_url = Column(String(500))
    is_active = Column(Boolean, default=True)
    last_login_at = Column(DateTime(timezone=True))

    # LINE 整合
    line_user_id = Column(String(100), unique=True, nullable=True, index=True)  # LINE 平台識別碼
    line_notify_enabled = Column(Boolean, default=True)  # 是否啟用 LINE 推播
    is_line_friend = Column(Boolean, default=False, nullable=False)  # 是否已加 OA 好友（沒加無法 push）
    line_friend_at = Column(DateTime(timezone=True), nullable=True)  # 加好友時間

    # 進階保護密碼（選填二因子）— 設了之後 OTP 通過還要再驗密碼
    # null 表示未啟用，登入維持單因子 OTP；有值（hashed）→ OTP + password 雙因子
    password_hash = Column(String(255), nullable=True)

    # Relationships
    consents = relationship("UserConsent", back_populates="user", lazy="selectin")
    vehicles = relationship("UserVehicle", back_populates="user", lazy="selectin")
    policies = relationship("Policy", back_populates="user", lazy="noload")
    accidents = relationship("Accident", back_populates="user", lazy="noload")
    claims = relationship("Claim", back_populates="user", lazy="noload")
    notifications = relationship("Notification", back_populates="user", lazy="noload")


class UserConsent(TimestampMixin, Base):
    __tablename__ = "user_consents"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False, index=True)
    consent_type = Column(String(50), nullable=False)  # privacy_policy, marketing, location, push_notification
    is_granted = Column(Boolean, nullable=False)
    granted_at = Column(DateTime(timezone=True))
    revoked_at = Column(DateTime(timezone=True))
    ip_address = Column(String(45))
    consent_version = Column(String(20))

    user = relationship("User", back_populates="consents")

    __table_args__ = (
        Index("ix_user_consents_user_type", "user_id", "consent_type"),
    )

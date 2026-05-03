"""
管理員帳號 + 客戶分配 + 操作日誌（獨立於客戶系統）
"""
from sqlalchemy import Column, String, Boolean, DateTime, Text, ForeignKey, Index
from sqlalchemy.orm import relationship
from app.database import Base, TimestampMixin, generate_uuid
from datetime import datetime, timezone


class AdminUser(TimestampMixin, Base):
    """管理員帳號（與客戶完全分離）"""
    __tablename__ = "admin_users"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    username = Column(String(50), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    display_name = Column(String(100))
    email = Column(String(255))
    phone = Column(String(20))
    role = Column(String(20), nullable=False, default="agent")  # super_admin / agent
    is_active = Column(Boolean, default=True)
    api_key = Column(String(64), unique=True, index=True)  # 業務員 API Key
    ip_whitelist = Column(Text)  # 允許的 IP，逗號分隔，空=不限制
    last_login_at = Column(DateTime)
    login_fail_count = Column(String(10), default="0")  # 連續失敗次數

    # 關聯
    assigned_customers = relationship("AgentCustomer", back_populates="agent", lazy="selectin")
    audit_logs = relationship("AuditLog", back_populates="admin_user", lazy="noload")


class AgentCustomer(TimestampMixin, Base):
    """業務員-客戶對應表（Row-Level Security）"""
    __tablename__ = "agent_customers"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    agent_id = Column(String(36), ForeignKey("admin_users.id"), nullable=False, index=True)
    customer_id = Column(String(36), ForeignKey("users.id"), nullable=False, index=True)
    assigned_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    assigned_by = Column(String(36))  # 分配者（super_admin）的 ID

    agent = relationship("AdminUser", back_populates="assigned_customers")
    customer = relationship("User")

    __table_args__ = (
        Index("ix_agent_customer_unique", "agent_id", "customer_id", unique=True),
    )


class AuditLog(TimestampMixin, Base):
    """操作審計日誌"""
    __tablename__ = "audit_logs"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    admin_user_id = Column(String(36), ForeignKey("admin_users.id"), nullable=False, index=True)
    action = Column(String(50), nullable=False)  # login/view/create/update/delete/export
    target_type = Column(String(30))  # customer/policy/claim/vehicle
    target_id = Column(String(36))
    detail = Column(Text)
    ip_address = Column(String(45))
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc), index=True)

    admin_user = relationship("AdminUser", back_populates="audit_logs")

from sqlalchemy import Column, String, Boolean, DateTime, Text, ForeignKey, Index
from sqlalchemy.orm import relationship
from app.database import Base, TimestampMixin, generate_uuid
from datetime import datetime, timezone


class Notification(TimestampMixin, Base):
    __tablename__ = "notifications"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    title = Column(String(200), nullable=False)
    body = Column(Text, nullable=False)
    notification_type = Column(String(30), nullable=False)
    # renewal_reminder, claim_update, accident_alert, inspection_reminder, system, payment
    reference_type = Column(String(30))  # policy, claim, accident
    reference_id = Column(String(36))
    is_read = Column(Boolean, default=False)
    read_at = Column(DateTime(timezone=True))
    sent_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    channel = Column(String(20), default="in_app")  # push, sms, email, in_app

    user = relationship("User", back_populates="notifications")

    __table_args__ = (
        Index("ix_notifications_user_read", "user_id", "is_read"),
        Index("ix_notifications_user_date", "user_id", "created_at"),
    )

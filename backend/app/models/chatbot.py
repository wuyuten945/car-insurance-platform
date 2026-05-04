from sqlalchemy import Column, String, DateTime, Float, Integer, Text, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base, TimestampMixin, generate_uuid
from datetime import datetime, timezone


class ChatbotSession(TimestampMixin, Base):
    __tablename__ = "chatbot_sessions"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False, index=True)
    status = Column(String(20), nullable=False, default="active")  # active, closed, transferred_to_human
    started_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    ended_at = Column(DateTime(timezone=True))
    intent_summary = Column(String(200))
    satisfaction_rating = Column(Integer)  # 1-5

    messages = relationship("ChatbotMessage", back_populates="session", lazy="selectin", order_by="ChatbotMessage.created_at")


class ChatbotMessage(TimestampMixin, Base):
    __tablename__ = "chatbot_messages"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    session_id = Column(String(36), ForeignKey("chatbot_sessions.id"), nullable=False, index=True)
    sender = Column(String(10), nullable=False)  # user, bot, agent
    content = Column(Text, nullable=False)
    intent = Column(String(50))
    confidence = Column(Float)

    session = relationship("ChatbotSession", back_populates="messages")

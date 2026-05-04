from sqlalchemy import Column, String, Boolean, DateTime, Float, Integer, Text, ForeignKey, Index
from sqlalchemy.orm import relationship
from app.database import Base, TimestampMixin, generate_uuid
from datetime import datetime, timezone


class Accident(TimestampMixin, Base):
    __tablename__ = "accidents"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    vehicle_id = Column(String(36), ForeignKey("user_vehicles.id"))
    policy_id = Column(String(36), ForeignKey("policies.id"))
    status = Column(String(30), nullable=False, default="reported")  # reported, in_progress, claim_filed, resolved
    occurred_at = Column(DateTime(timezone=True), nullable=False)
    reported_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    latitude = Column(Float)
    longitude = Column(Float)
    address = Column(String(500))
    description = Column(Text)

    # 事故類型（第一層）
    accident_type = Column(String(30))  # rear_end, side, head_on, scrape, parking, single, other
    # 我方情況（第二層）
    my_situation = Column(String(30))  # straight, turning_left, turning_right, reversing, parked, accelerating, other
    # 環境條件（第三層，JSON 存放複選）
    environment_conditions = Column(Text)  # JSON: {time_of_day, weather, road_surface, traffic_signal, road_type}
    # 補充說明（第四層）
    supplementary_notes = Column(Text)

    injury_involved = Column(Boolean, default=False)
    police_called = Column(Boolean, default=False)
    police_report_number = Column(String(50))
    counterparty_name = Column(String(100))
    counterparty_phone = Column(String(20))
    counterparty_plate = Column(String(20))
    counterparty_insurer = Column(String(100))
    counterparty_license = Column(String(50))
    emergency_contacts_notified = Column(Boolean, default=False)

    user = relationship("User", back_populates="accidents")
    photos = relationship("AccidentPhoto", back_populates="accident", lazy="selectin")

    __table_args__ = (
        Index("ix_accidents_user_status", "user_id", "status"),
    )


class AccidentPhoto(TimestampMixin, Base):
    __tablename__ = "accident_photos"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    accident_id = Column(String(36), ForeignKey("accidents.id"), nullable=False, index=True)
    photo_url = Column(String(500), nullable=False)
    photo_type = Column(String(30))  # scene_overview, damage_close, license_plate, road_condition, document, cctv_location
    latitude = Column(Float)
    longitude = Column(Float)
    taken_at = Column(DateTime(timezone=True))
    watermark_text = Column(String(200))
    file_size_bytes = Column(Integer)

    accident = relationship("Accident", back_populates="photos")

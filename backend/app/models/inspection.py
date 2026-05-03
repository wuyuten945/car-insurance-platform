from sqlalchemy import Column, String, Boolean, Float, Text
from app.database import Base, TimestampMixin, generate_uuid


class InspectionStation(TimestampMixin, Base):
    __tablename__ = "inspection_stations"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    station_name = Column(String(200), nullable=False)
    station_type = Column(String(20), default="inspection")  # supervision=監理站, inspection=公立驗車廠, private=民間驗車廠
    address = Column(String(500))
    city = Column(String(20))
    district = Column(String(20))
    phone = Column(String(20))
    latitude = Column(Float)
    longitude = Column(Float)
    operating_hours = Column(String(100))
    supports_motorcycle = Column(Boolean, default=False)
    supports_heavy = Column(Boolean, default=False)
    booking_url = Column(String(500))
    services = Column(Text)  # 提供服務項目，逗號分隔

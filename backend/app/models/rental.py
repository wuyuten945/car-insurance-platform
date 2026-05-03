from sqlalchemy import Column, String, Boolean, Float, Numeric
from app.database import Base, TimestampMixin, generate_uuid


class RentalCar(TimestampMixin, Base):
    __tablename__ = "rental_cars"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    company_name = Column(String(100), nullable=False)
    branch_name = Column(String(100))
    address = Column(String(500))
    phone = Column(String(20))
    latitude = Column(Float)
    longitude = Column(Float)
    daily_rate_min = Column(Numeric(8, 2))
    daily_rate_max = Column(Numeric(8, 2))
    operating_hours = Column(String(100))
    has_delivery = Column(Boolean, default=False)
    is_24hr = Column(Boolean, default=False)
    is_partner = Column(Boolean, default=False)
    rating = Column(Numeric(2, 1))

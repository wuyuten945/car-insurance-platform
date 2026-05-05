from sqlalchemy import Column, String, Integer, Boolean, Date, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base, TimestampMixin, generate_uuid


class UserVehicle(TimestampMixin, Base):
    __tablename__ = "user_vehicles"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False, index=True)
    plate_number = Column(String(20), nullable=False)
    brand = Column(String(50))
    model = Column(String(50))
    year = Column(Integer)
    manufacture_month = Column(Integer)            # 出廠月份 1-12（搭配 year 表示出廠年月）
    color = Column(String(20))
    vin = Column(String(50))
    engine_cc = Column(Integer)
    is_primary = Column(Boolean, default=False)
    vehicle_type = Column(String(50))  # 車輛型式（監理分類：自用小客車、營業大客車等）
    fuel_type = Column(String(20))    # 燃料種類（汽油、柴油、電動、油電）

    # 行照資料
    registration_image_url = Column(String(500))  # 行照圖片路徑
    registration_date = Column(Date)               # 原發照日期
    reissue_date = Column(Date)                    # 換/補照日期（補發或更換新行照）
    registration_expiry = Column(Date)             # 行照有效期限（= 驗車到期日）
    last_inspection_date = Column(Date)            # 上次驗車日期

    user = relationship("User", back_populates="vehicles")
    policies = relationship("Policy", back_populates="vehicle", lazy="noload")

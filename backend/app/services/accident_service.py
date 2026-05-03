from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from fastapi import UploadFile
from app.models.accident import Accident, AccidentPhoto
from app.schemas.accident import AccidentCreate, NearbyResource
from app.core.storage import storage
from app.exceptions import NotFoundError


class AccidentService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_accident(self, user_id: str, data: AccidentCreate) -> Accident:
        accident = Accident(
            user_id=user_id,
            **data.model_dump(),
        )
        self.db.add(accident)
        await self.db.flush()
        return accident

    async def get_accident(self, user_id: str, accident_id: str) -> Accident:
        result = await self.db.execute(
            select(Accident).options(
                selectinload(Accident.photos)
            ).where(Accident.id == accident_id, Accident.user_id == user_id)
        )
        accident = result.scalar_one_or_none()
        if not accident:
            raise NotFoundError("事故記錄不存在")
        return accident

    async def list_accidents(self, user_id: str) -> list[Accident]:
        result = await self.db.execute(
            select(Accident).options(
                selectinload(Accident.photos)
            ).where(Accident.user_id == user_id)
            .order_by(Accident.occurred_at.desc())
        )
        return list(result.scalars().all())

    async def upload_photo(
        self, accident_id: str, file: UploadFile, photo_type: str = None,
        latitude: float = None, longitude: float = None,
    ) -> AccidentPhoto:
        file_url = await storage.upload(file, subfolder=f"accidents/{accident_id}")

        now = datetime.now(timezone.utc)
        watermark_parts = [now.strftime("%Y-%m-%d %H:%M:%S")]
        if latitude and longitude:
            watermark_parts.append(f"GPS: {latitude:.6f}, {longitude:.6f}")
        watermark_parts.append(f"案件: {accident_id[:8]}")
        watermark_text = " | ".join(watermark_parts)

        photo = AccidentPhoto(
            accident_id=accident_id,
            photo_url=file_url,
            photo_type=photo_type,
            latitude=latitude,
            longitude=longitude,
            taken_at=now,
            watermark_text=watermark_text,
            file_size_bytes=file.size if file.size else 0,
        )
        self.db.add(photo)
        await self.db.flush()
        return photo

    async def get_nearby_resources(
        self, latitude: float, longitude: float
    ) -> list[NearbyResource]:
        """回傳附近資源（Mock 資料，生產環境串接 Google Maps API）"""
        resources = [
            NearbyResource(
                name="中正一分局",
                address="台北市中正區忠孝東路一段7號",
                phone="02-23411476",
                distance_km=0.8,
                latitude=25.0425,
                longitude=121.5240,
                resource_type="police_station",
            ),
            NearbyResource(
                name="大安分局",
                address="台北市大安區仁愛路四段27巷28號",
                phone="02-27071270",
                distance_km=1.5,
                latitude=25.0390,
                longitude=121.5450,
                resource_type="police_station",
            ),
            NearbyResource(
                name="信義拖吊場",
                address="台北市信義區松德路300號",
                phone="02-87895678",
                distance_km=2.0,
                latitude=25.0310,
                longitude=121.5680,
                resource_type="tow_company",
            ),
            NearbyResource(
                name="24H 全方位拖吊服務",
                address="台北市中山區民生東路三段",
                phone="0800-000-123",
                distance_km=3.2,
                latitude=25.0580,
                longitude=121.5420,
                resource_type="tow_company",
            ),
            NearbyResource(
                name="台北原廠修車中心",
                address="台北市內湖區瑞光路513號",
                phone="02-27991234",
                distance_km=4.5,
                latitude=25.0780,
                longitude=121.5690,
                resource_type="repair_shop",
            ),
        ]
        return resources

from decimal import Decimal
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.rental import RentalCar
from app.schemas.rental import RentalCostEstimate


class RentalService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def list_nearby(
        self, latitude: float, longitude: float, radius_km: float = 5.0
    ) -> list[RentalCar]:
        """查詢附近租車行（開發用簡易距離計算）"""
        result = await self.db.execute(
            select(RentalCar).where(RentalCar.latitude.isnot(None))
        )
        cars = list(result.scalars().all())

        # 簡易距離篩選（生產環境用 PostGIS）
        import math
        nearby = []
        for car in cars:
            dist = self._haversine(latitude, longitude, car.latitude, car.longitude)
            if dist <= radius_km:
                car.distance_km = round(dist, 1)
                nearby.append(car)

        nearby.sort(key=lambda c: (not c.is_partner, not c.is_24hr, c.distance_km))
        return nearby

    def estimate_cost(
        self, daily_rate: Decimal, rental_days: int, insurance_fee: Decimal = Decimal("0")
    ) -> RentalCostEstimate:
        total = daily_rate * rental_days + insurance_fee
        return RentalCostEstimate(
            rental_days=rental_days,
            daily_rate=daily_rate,
            insurance_fee=insurance_fee,
            total_cost=total,
        )

    @staticmethod
    def _haversine(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        import math
        R = 6371
        dlat = math.radians(lat2 - lat1)
        dlon = math.radians(lon2 - lon1)
        a = math.sin(dlat / 2) ** 2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2) ** 2
        return R * 2 * math.asin(math.sqrt(a))

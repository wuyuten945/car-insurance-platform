import math
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_
from app.models.inspection import InspectionStation
from app.schemas.inspection import InspectionStationOut


def _haversine(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """計算兩點間的距離（公里）"""
    R = 6371.0
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (math.sin(dlat / 2) ** 2 +
         math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) *
         math.sin(dlon / 2) ** 2)
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def _google_map_url(name: str, lat: float | None, lon: float | None, address: str | None) -> str:
    """產生 Google Maps 連結"""
    if lat and lon:
        return f"https://www.google.com/maps/search/?api=1&query={lat},{lon}"
    if address:
        import urllib.parse
        return f"https://www.google.com/maps/search/?api=1&query={urllib.parse.quote(address)}"
    return ""


def _to_out(station: InspectionStation, user_lat: float = None, user_lon: float = None) -> InspectionStationOut:
    """轉換為回傳格式，含距離和 Google Map 連結"""
    distance = None
    if user_lat and user_lon and station.latitude and station.longitude:
        distance = round(_haversine(user_lat, user_lon, station.latitude, station.longitude), 1)

    return InspectionStationOut(
        id=station.id,
        station_name=station.station_name,
        station_type=station.station_type or "inspection",
        address=station.address,
        city=station.city,
        district=station.district,
        phone=station.phone,
        latitude=station.latitude,
        longitude=station.longitude,
        operating_hours=station.operating_hours,
        supports_motorcycle=station.supports_motorcycle,
        supports_heavy=station.supports_heavy,
        booking_url=station.booking_url,
        services=station.services,
        distance_km=distance,
        google_map_url=_google_map_url(station.station_name, station.latitude, station.longitude, station.address),
    )


class InspectionService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def list_stations(
        self,
        city: str = None,
        station_type: str = None,
    ) -> list[InspectionStation]:
        query = select(InspectionStation)
        if city:
            query = query.where(InspectionStation.city == city)
        if station_type:
            query = query.where(InspectionStation.station_type == station_type)
        query = query.order_by(InspectionStation.city, InspectionStation.station_name)
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def search_stations(
        self,
        keyword: str = None,
        city: str = None,
        station_type: str = None,
        latitude: float = None,
        longitude: float = None,
        radius_km: float = 50,
    ) -> list[InspectionStationOut]:
        """搜尋站點：支援關鍵字、縣市、類型、附近"""
        query = select(InspectionStation)

        if city:
            query = query.where(InspectionStation.city == city)
        if station_type:
            query = query.where(InspectionStation.station_type == station_type)
        if keyword:
            pattern = f"%{keyword}%"
            query = query.where(
                or_(
                    InspectionStation.station_name.contains(keyword),
                    InspectionStation.address.contains(keyword),
                    InspectionStation.city.contains(keyword),
                    InspectionStation.district.contains(keyword),
                    InspectionStation.services.contains(keyword),
                )
            )

        query = query.order_by(InspectionStation.city, InspectionStation.station_name)
        result = await self.db.execute(query)
        stations = list(result.scalars().all())

        # 轉換並計算距離
        items = [_to_out(s, latitude, longitude) for s in stations]

        # 若有定位，過濾範圍並按距離排序
        if latitude and longitude:
            items = [i for i in items if i.distance_km is not None and i.distance_km <= radius_km]
            items.sort(key=lambda x: x.distance_km or 9999)

        return items

    async def nearby_stations(
        self,
        latitude: float,
        longitude: float,
        radius_km: float = 30,
        station_type: str = None,
    ) -> list[InspectionStationOut]:
        """以 GPS 座標搜尋附近站點"""
        return await self.search_stations(
            latitude=latitude,
            longitude=longitude,
            radius_km=radius_km,
            station_type=station_type,
        )

    async def get_cities(self) -> list[str]:
        """取得所有縣市列表"""
        result = await self.db.execute(
            select(InspectionStation.city)
            .where(InspectionStation.city.isnot(None))
            .distinct()
            .order_by(InspectionStation.city)
        )
        return [row[0] for row in result.all()]

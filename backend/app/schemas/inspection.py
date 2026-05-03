from pydantic import BaseModel


class InspectionStationOut(BaseModel):
    id: str
    station_name: str
    station_type: str = "inspection"
    address: str | None = None
    city: str | None = None
    district: str | None = None
    phone: str | None = None
    latitude: float | None = None
    longitude: float | None = None
    operating_hours: str | None = None
    supports_motorcycle: bool = False
    supports_heavy: bool = False
    booking_url: str | None = None
    services: str | None = None
    distance_km: float | None = None
    google_map_url: str | None = None

    model_config = {"from_attributes": True}

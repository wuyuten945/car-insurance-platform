from pydantic import BaseModel
from datetime import datetime


class AccidentCreate(BaseModel):
    vehicle_id: str | None = None
    policy_id: str | None = None
    occurred_at: datetime
    latitude: float | None = None
    longitude: float | None = None
    address: str | None = None
    description: str | None = None
    accident_type: str | None = None
    my_situation: str | None = None
    environment_conditions: str | None = None
    supplementary_notes: str | None = None
    injury_involved: bool = False
    police_called: bool = False
    police_report_number: str | None = None
    counterparty_name: str | None = None
    counterparty_phone: str | None = None
    counterparty_plate: str | None = None
    counterparty_insurer: str | None = None


class AccidentPhotoOut(BaseModel):
    id: str
    photo_url: str
    photo_type: str | None = None
    taken_at: datetime | None = None
    watermark_text: str | None = None

    model_config = {"from_attributes": True}


class AccidentOut(BaseModel):
    id: str
    status: str
    occurred_at: datetime
    reported_at: datetime
    latitude: float | None = None
    longitude: float | None = None
    address: str | None = None
    description: str | None = None
    accident_type: str | None = None
    injury_involved: bool
    police_called: bool
    police_report_number: str | None = None
    counterparty_name: str | None = None
    counterparty_plate: str | None = None
    photos: list[AccidentPhotoOut] = []
    created_at: datetime

    model_config = {"from_attributes": True}


class NearbyResource(BaseModel):
    name: str
    address: str
    phone: str | None = None
    distance_km: float | None = None
    latitude: float | None = None
    longitude: float | None = None
    resource_type: str  # police_station, tow_company, repair_shop

from pydantic import BaseModel
from decimal import Decimal


class RentalCarOut(BaseModel):
    id: str
    company_name: str
    branch_name: str | None = None
    address: str | None = None
    phone: str | None = None
    latitude: float | None = None
    longitude: float | None = None
    daily_rate_min: Decimal | None = None
    daily_rate_max: Decimal | None = None
    operating_hours: str | None = None
    has_delivery: bool = False
    is_24hr: bool = False
    is_partner: bool = False
    rating: Decimal | None = None
    distance_km: float | None = None

    model_config = {"from_attributes": True}


class RentalCostEstimate(BaseModel):
    rental_days: int
    daily_rate: Decimal
    insurance_fee: Decimal = Decimal("0")
    total_cost: Decimal
    claimable_amount: Decimal | None = None

from pydantic import BaseModel
from datetime import date, datetime, time
from decimal import Decimal


class PolicyItemOut(BaseModel):
    id: str
    item_name: str
    coverage_limit: Decimal | None = None
    deductible: Decimal | None = None
    premium: Decimal | None = None
    is_active: bool = True
    description: str | None = None
    exclusions: str | None = None

    model_config = {"from_attributes": True}


class PolicyOut(BaseModel):
    id: str
    insurer_name: str
    policy_number: str
    status: str
    start_date: date
    end_date: date
    start_time: time | None = None
    end_time: time | None = None
    compulsory_start_date: date | None = None
    compulsory_end_date: date | None = None
    compulsory_start_time: time | None = None
    compulsory_end_time: time | None = None
    total_premium: Decimal | None = None
    vehicle_plate: str | None = None
    vehicle_brand: str | None = None
    vehicle_model: str | None = None
    days_remaining: int | None = None
    items: list[PolicyItemOut] = []

    model_config = {"from_attributes": True}


class PolicyDetailOut(PolicyOut):
    document_url: str | None = None
    created_at: datetime


class ExclusionItem(BaseModel):
    item_name: str
    category: str  # 車體損失不賠, 第三人責任不賠, 竊盜不賠
    description: str
    scenario: str  # 情境說明


class ExclusionListOut(BaseModel):
    policy_id: str
    insurer_name: str
    exclusions: list[ExclusionItem]


class RenewalQuoteOut(BaseModel):
    id: str
    insurer_name: str
    insurer_logo_url: str | None = None
    quoted_premium: Decimal
    coverage_details: dict | None = None
    rating: Decimal | None = None
    claim_speed_days: Decimal | None = None
    features: str | None = None
    valid_until: date | None = None
    is_selected: bool = False

    model_config = {"from_attributes": True}


class PaymentMethodOut(BaseModel):
    id: str
    method_type: str
    card_brand: str | None = None
    last_four: str | None = None
    bank_name: str | None = None
    is_default: bool

    model_config = {"from_attributes": True}


class PaymentMethodCreate(BaseModel):
    method_type: str
    card_brand: str | None = None
    last_four: str | None = None
    bank_name: str | None = None
    is_default: bool = False


# ===== Policy CRUD Schemas =====

class PolicyItemCreate(BaseModel):
    item_name: str
    coverage_limit: Decimal | None = None
    deductible: Decimal | None = None
    premium: Decimal | None = None
    is_active: bool = True
    description: str | None = None
    exclusions: str | None = None  # JSON string


class PolicyItemUpdate(BaseModel):
    item_name: str | None = None
    coverage_limit: Decimal | None = None
    deductible: Decimal | None = None
    premium: Decimal | None = None
    is_active: bool | None = None
    description: str | None = None
    exclusions: str | None = None


class PolicyCreate(BaseModel):
    vehicle_id: str | None = None
    insurer_name: str
    policy_number: str
    status: str = "active"
    start_date: date
    end_date: date
    start_time: time | None = None
    end_time: time | None = None
    compulsory_start_date: date | None = None
    compulsory_end_date: date | None = None
    compulsory_start_time: time | None = None
    compulsory_end_time: time | None = None
    total_premium: Decimal | None = None
    document_url: str | None = None
    items: list[PolicyItemCreate] = []


class PolicyUpdate(BaseModel):
    vehicle_id: str | None = None
    insurer_name: str | None = None
    policy_number: str | None = None
    status: str | None = None
    start_date: date | None = None
    end_date: date | None = None
    start_time: time | None = None
    end_time: time | None = None
    compulsory_start_date: date | None = None
    compulsory_end_date: date | None = None
    compulsory_start_time: time | None = None
    compulsory_end_time: time | None = None
    total_premium: Decimal | None = None
    document_url: str | None = None

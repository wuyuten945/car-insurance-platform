from pydantic import BaseModel, Field
from datetime import date, datetime
from decimal import Decimal


class DesiredItem(BaseModel):
    """客戶勾選的單個保障項目"""
    name: str
    limit: int | None = None     # 保額（如 5000000 = 500 萬）
    note: str | None = None


class QuoteRequestCreate(BaseModel):
    vehicle_id: str | None = None
    source_policy_id: str | None = None     # 「跟原保單一樣」用此
    use_existing_policy: bool = False
    desired_items: list[DesiredItem] = []
    driver_age: int | None = None
    claims_count_3y: int | None = None       # 過去 3 年出險次數
    surcharge_pct: Decimal | None = None     # 客戶自知的加費%
    notes: str | None = None


class QuoteResponseOut(BaseModel):
    id: str
    insurer_name: str
    quoted_premium: Decimal
    coverage_details: list[dict] | None = None
    valid_until: date | None = None
    notes: str | None = None
    is_recommended: bool = False

    model_config = {"from_attributes": True}


class QuoteRequestOut(BaseModel):
    id: str
    user_id: str
    vehicle_id: str | None = None
    source_policy_id: str | None = None
    use_existing_policy: bool = False
    desired_items: list[dict] | None = None
    driver_age: int | None = None
    claims_count_3y: int | None = None
    surcharge_pct: Decimal | None = None
    notes: str | None = None

    assigned_to_admin_id: str | None = None
    assigned_admin_name: str | None = None    # 衍生

    status: str
    submitted_at: datetime
    quoted_at: datetime | None = None
    completed_at: datetime | None = None

    responses: list[QuoteResponseOut] = []
    # 衍生欄位（前台顯示方便用）
    customer_name: str | None = None
    vehicle_plate: str | None = None

    model_config = {"from_attributes": True}


class QuoteResponseCreate(BaseModel):
    insurer_name: str
    quoted_premium: Decimal
    coverage_details: list[dict] | None = None
    valid_until: date | None = None
    notes: str | None = None
    is_recommended: bool = False


class QuoteRequestStatusUpdate(BaseModel):
    status: str = Field(..., description="pending / in_progress / quoted / completed / cancelled")

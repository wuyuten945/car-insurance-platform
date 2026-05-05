from pydantic import BaseModel, EmailStr, field_validator
from datetime import datetime, date


class UserOut(BaseModel):
    id: str
    phone: str | None = None
    name: str | None = None
    email: str | None = None
    birth_date: datetime | None = None
    address: str | None = None
    registered_address: str | None = None
    emergency_contact_name: str | None = None
    emergency_contact_phone: str | None = None
    emergency_contact_relation: str | None = None
    license_number: str | None = None
    license_expiry: datetime | None = None
    avatar_url: str | None = None
    created_at: datetime
    # 給前端用來判斷是否需要導向 /onboarding
    has_id_number: bool = False
    is_profile_complete: bool = False

    model_config = {"from_attributes": True}

    @classmethod
    def model_validate(cls, obj, **kwargs):
        out = super().model_validate(obj, **kwargs)
        # 動態填入兩個衍生欄位
        out.has_id_number = bool(getattr(obj, "id_number_hash", None))
        out.is_profile_complete = bool(
            out.name and out.birth_date and out.has_id_number
        )
        return out


class UserProfileUpdate(BaseModel):
    name: str | None = None
    email: str | None = None
    phone: str | None = None
    id_number: str | None = None  # 明文輸入，後端會 hash 存
    birth_date: datetime | None = None
    address: str | None = None
    registered_address: str | None = None
    emergency_contact_name: str | None = None
    emergency_contact_phone: str | None = None
    emergency_contact_relation: str | None = None
    license_number: str | None = None
    license_expiry: datetime | None = None

    @field_validator("id_number")
    @classmethod
    def _check_id_number(cls, v):
        if not v:
            return v
        v = v.strip().upper()
        # 台灣身份證：1 個英文字母 + 9 個數字（不做 checksum 嚴格驗證，給寬鬆 regex）
        import re as _re
        if not _re.match(r"^[A-Z][0-9]{9}$", v):
            raise ValueError("身份證字號格式不正確（1 英文字母 + 9 數字）")
        return v

    @field_validator("phone")
    @classmethod
    def _check_phone(cls, v):
        if not v:
            return v
        import re as _re
        cleaned = _re.sub(r"[\s\-\(\)]", "", v)
        if cleaned.startswith("+886"):
            cleaned = "0" + cleaned[4:]
        if not _re.match(r"^09\d{8}$", cleaned):
            raise ValueError("手機格式不正確（09 開頭，10 碼）")
        return cleaned


class ConsentUpdate(BaseModel):
    consent_type: str  # privacy_policy, marketing, location, push_notification
    is_granted: bool


class ConsentOut(BaseModel):
    id: str
    consent_type: str
    is_granted: bool
    granted_at: datetime | None = None
    revoked_at: datetime | None = None

    model_config = {"from_attributes": True}


class VehicleCreate(BaseModel):
    plate_number: str
    brand: str | None = None
    model: str | None = None
    year: int | None = None
    manufacture_month: int | None = None
    color: str | None = None
    vin: str | None = None
    engine_cc: int | None = None
    is_primary: bool = False
    vehicle_type: str | None = None
    fuel_type: str | None = None
    registration_date: date | None = None
    reissue_date: date | None = None
    registration_expiry: date | None = None
    last_inspection_date: date | None = None


class VehicleUpdate(BaseModel):
    plate_number: str | None = None
    brand: str | None = None
    model: str | None = None
    year: int | None = None
    manufacture_month: int | None = None
    color: str | None = None
    vin: str | None = None
    engine_cc: int | None = None
    is_primary: bool | None = None
    vehicle_type: str | None = None
    fuel_type: str | None = None
    registration_date: date | None = None
    reissue_date: date | None = None
    registration_expiry: date | None = None
    last_inspection_date: date | None = None


class VehicleOut(BaseModel):
    id: str
    plate_number: str
    brand: str | None = None
    model: str | None = None
    year: int | None = None
    manufacture_month: int | None = None
    color: str | None = None
    vin: str | None = None
    engine_cc: int | None = None
    is_primary: bool
    vehicle_type: str | None = None
    fuel_type: str | None = None
    registration_image_url: str | None = None
    registration_date: date | None = None
    reissue_date: date | None = None
    registration_expiry: date | None = None
    last_inspection_date: date | None = None
    created_at: datetime

    model_config = {"from_attributes": True}

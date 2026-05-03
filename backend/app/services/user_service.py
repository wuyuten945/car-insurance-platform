import uuid
from datetime import datetime, date, timedelta, timezone
from pathlib import Path
from fastapi import UploadFile
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from sqlalchemy.orm import selectinload
from app.models.user import User, UserConsent
from app.models.vehicle import UserVehicle
from app.models.policy import Policy, PolicyItem
from app.schemas.user import UserProfileUpdate, ConsentUpdate, VehicleCreate, VehicleUpdate
from app.exceptions import NotFoundError, BadRequestError
from app.config import settings


class UserService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_profile(self, user_id: str) -> User:
        result = await self.db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
        if not user:
            raise NotFoundError("使用者不存在")
        return user

    async def update_profile(self, user_id: str, data: UserProfileUpdate) -> User:
        import hashlib
        user = await self.get_profile(user_id)
        update_data = data.model_dump(exclude_unset=True)

        # id_number 是明文輸入欄位，要 hash 後存到 id_number_hash（不存明文）
        if "id_number" in update_data:
            idn = update_data.pop("id_number")
            if idn:
                user.id_number_hash = hashlib.sha256(idn.strip().encode()).hexdigest()
            else:
                user.id_number_hash = None

        # phone/email 撞 unique 的話要明確報錯（避免 IntegrityError 從 SQLAlchemy 拋）
        if "phone" in update_data and update_data["phone"] != user.phone:
            new_phone = update_data["phone"]
            if new_phone:
                dup = await self.db.execute(
                    select(User).where(User.phone == new_phone, User.id != user_id)
                )
                if dup.scalar_one_or_none():
                    raise BadRequestError("此手機號碼已被其他帳號使用")
        if "email" in update_data and update_data["email"] and update_data["email"] != user.email:
            new_email = update_data["email"]
            dup = await self.db.execute(
                select(User).where(User.email == new_email, User.id != user_id)
            )
            if dup.scalar_one_or_none():
                raise BadRequestError("此 Email 已被其他帳號使用")

        for key, value in update_data.items():
            setattr(user, key, value)
        await self.db.flush()
        return user

    async def update_consent(self, user_id: str, data: ConsentUpdate) -> UserConsent:
        result = await self.db.execute(
            select(UserConsent).where(
                and_(UserConsent.user_id == user_id, UserConsent.consent_type == data.consent_type)
            )
        )
        consent = result.scalar_one_or_none()

        now = datetime.now(timezone.utc)
        if consent:
            consent.is_granted = data.is_granted
            if data.is_granted:
                consent.granted_at = now
                consent.revoked_at = None
            else:
                consent.revoked_at = now
        else:
            consent = UserConsent(
                user_id=user_id,
                consent_type=data.consent_type,
                is_granted=data.is_granted,
                granted_at=now if data.is_granted else None,
            )
            self.db.add(consent)

        await self.db.flush()
        return consent

    async def get_consents(self, user_id: str) -> list[UserConsent]:
        result = await self.db.execute(
            select(UserConsent).where(UserConsent.user_id == user_id)
        )
        return list(result.scalars().all())

    # Vehicle CRUD
    async def list_vehicles(self, user_id: str) -> list[UserVehicle]:
        result = await self.db.execute(
            select(UserVehicle).where(UserVehicle.user_id == user_id)
        )
        return list(result.scalars().all())

    async def create_vehicle(self, user_id: str, data: VehicleCreate) -> UserVehicle:
        vehicle = UserVehicle(user_id=user_id, **data.model_dump())
        if data.is_primary:
            await self._clear_primary_vehicle(user_id)
        self.db.add(vehicle)
        await self.db.flush()
        return vehicle

    async def update_vehicle(self, user_id: str, vehicle_id: str, data: VehicleCreate) -> UserVehicle:
        result = await self.db.execute(
            select(UserVehicle).where(
                and_(UserVehicle.id == vehicle_id, UserVehicle.user_id == user_id)
            )
        )
        vehicle = result.scalar_one_or_none()
        if not vehicle:
            raise NotFoundError("車輛不存在")

        update_data = data.model_dump(exclude_unset=True)
        if update_data.get("is_primary"):
            await self._clear_primary_vehicle(user_id)
        for key, value in update_data.items():
            setattr(vehicle, key, value)
        await self.db.flush()
        return vehicle

    async def delete_vehicle(self, user_id: str, vehicle_id: str) -> None:
        result = await self.db.execute(
            select(UserVehicle).where(
                and_(UserVehicle.id == vehicle_id, UserVehicle.user_id == user_id)
            )
        )
        vehicle = result.scalar_one_or_none()
        if not vehicle:
            raise NotFoundError("車輛不存在")
        await self.db.delete(vehicle)

    async def patch_vehicle(self, user_id: str, vehicle_id: str, data: VehicleUpdate) -> UserVehicle:
        """部分更新車輛欄位"""
        result = await self.db.execute(
            select(UserVehicle).where(
                and_(UserVehicle.id == vehicle_id, UserVehicle.user_id == user_id)
            )
        )
        vehicle = result.scalar_one_or_none()
        if not vehicle:
            raise NotFoundError("車輛不存在")
        update_data = data.model_dump(exclude_unset=True)
        if update_data.get("is_primary"):
            await self._clear_primary_vehicle(user_id)
        for key, value in update_data.items():
            setattr(vehicle, key, value)
        await self.db.flush()
        return vehicle

    async def upload_registration(self, user_id: str, vehicle_id: str, file: UploadFile) -> UserVehicle:
        """上傳行照（圖片或 PDF）"""
        from app.core.pdf_utils import is_pdf, pdf_to_images

        result = await self.db.execute(
            select(UserVehicle).where(
                and_(UserVehicle.id == vehicle_id, UserVehicle.user_id == user_id)
            )
        )
        vehicle = result.scalar_one_or_none()
        if not vehicle:
            raise NotFoundError("車輛不存在")

        allowed = ("image/jpeg", "image/png", "image/webp", "application/pdf")
        if file.content_type not in allowed:
            raise BadRequestError("僅支援 JPG/PNG/WebP/PDF 格式")

        ext = file.filename.rsplit(".", 1)[-1] if file.filename else "jpg"
        filename = f"registration_{vehicle_id}_{uuid.uuid4().hex[:8]}.{ext}"
        upload_dir = Path(settings.UPLOAD_DIR) / "registrations"
        upload_dir.mkdir(parents=True, exist_ok=True)

        filepath = upload_dir / filename
        content = await file.read()
        filepath.write_bytes(content)

        # PDF → 轉第一頁為 JPG 供顯示和 OCR
        if is_pdf(file.content_type, file.filename):
            images = pdf_to_images(str(filepath), str(upload_dir))
            if images:
                jpg_name = Path(images[0]).name
                vehicle.registration_image_url = f"/uploads/registrations/{jpg_name}"
            else:
                vehicle.registration_image_url = f"/uploads/registrations/{filename}"
        else:
            vehicle.registration_image_url = f"/uploads/registrations/{filename}"

        await self.db.flush()
        return vehicle

    async def get_inspection_status(self, user_id: str, vehicle_id: str) -> dict:
        """查詢車輛驗車狀態，含強制險有效性檢查"""
        result = await self.db.execute(
            select(UserVehicle).where(
                and_(UserVehicle.id == vehicle_id, UserVehicle.user_id == user_id)
            )
        )
        vehicle = result.scalar_one_or_none()
        if not vehicle:
            raise NotFoundError("車輛不存在")

        today = date.today()

        # 查詢此車輛的有效保單中是否含強制險
        policy_result = await self.db.execute(
            select(Policy)
            .options(selectinload(Policy.items))
            .where(
                and_(
                    Policy.user_id == user_id,
                    Policy.vehicle_id == vehicle_id,
                    Policy.status.in_(["active", "expiring"]),
                    Policy.end_date >= today,
                )
            )
        )
        policies = list(policy_result.scalars().all())

        has_compulsory = False
        compulsory_expiry = None
        for p in policies:
            for item in p.items:
                if "強制" in item.item_name and item.is_active:
                    has_compulsory = True
                    if compulsory_expiry is None or p.end_date > compulsory_expiry:
                        compulsory_expiry = p.end_date

        # 驗車到期狀態
        registration_expiry = vehicle.registration_expiry
        days_to_inspection = None
        inspection_status = "unknown"
        if registration_expiry:
            days_to_inspection = (registration_expiry - today).days
            if days_to_inspection < 0:
                inspection_status = "overdue"
            elif days_to_inspection <= 30:
                inspection_status = "urgent"
            elif days_to_inspection <= 60:
                inspection_status = "upcoming"
            else:
                inspection_status = "ok"

        # 強制險剩餘天數（驗車需 >= 30 天）
        compulsory_days = (compulsory_expiry - today).days if compulsory_expiry else 0
        compulsory_valid_for_inspection = has_compulsory and compulsory_days >= 30

        # 可驗車區間（到期前 30 天 ~ 到期後 30 天）
        inspect_window_start = None
        inspect_window_end = None
        in_inspection_window = False
        if registration_expiry:
            inspect_window_start = (registration_expiry - timedelta(days=30)).isoformat()
            inspect_window_end = (registration_expiry + timedelta(days=30)).isoformat()
            in_inspection_window = -30 <= days_to_inspection <= 30

        can_inspect = compulsory_valid_for_inspection
        warnings = []
        if not has_compulsory:
            warnings.append("無有效強制汽車責任保險，無法辦理驗車。請先投保強制險。")
        elif not compulsory_valid_for_inspection:
            warnings.append(f"強制險剩餘僅 {compulsory_days} 天（需 >= 30 天），請先續保強制險再驗車。")
        if registration_expiry and days_to_inspection is not None and days_to_inspection < 0:
            if days_to_inspection >= -30:
                warnings.append(f"行照已逾期 {abs(days_to_inspection)} 天，逾期後 30 天內仍可驗車，請儘速辦理。")
            else:
                warnings.append(f"行照已逾期 {abs(days_to_inspection)} 天，已超過可驗車期限，可能面臨罰鍰。")

        return {
            "vehicle_id": vehicle.id,
            "plate_number": vehicle.plate_number,
            "brand": vehicle.brand,
            "model": vehicle.model,
            "registration_expiry": registration_expiry.isoformat() if registration_expiry else None,
            "days_to_inspection": days_to_inspection,
            "inspection_status": inspection_status,
            "inspect_window_start": inspect_window_start,
            "inspect_window_end": inspect_window_end,
            "in_inspection_window": in_inspection_window,
            "has_compulsory_insurance": has_compulsory,
            "compulsory_expiry": compulsory_expiry.isoformat() if compulsory_expiry else None,
            "compulsory_days_remaining": compulsory_days,
            "compulsory_valid_for_inspection": compulsory_valid_for_inspection,
            "can_inspect": can_inspect,
            "warnings": warnings,
            "registration_image_url": vehicle.registration_image_url,
            "last_inspection_date": vehicle.last_inspection_date.isoformat() if vehicle.last_inspection_date else None,
        }

    async def _clear_primary_vehicle(self, user_id: str):
        result = await self.db.execute(
            select(UserVehicle).where(
                and_(UserVehicle.user_id == user_id, UserVehicle.is_primary == True)
            )
        )
        for v in result.scalars().all():
            v.is_primary = False

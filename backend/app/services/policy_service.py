import json
from datetime import date
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from sqlalchemy.orm import selectinload
from app.models.policy import Policy, PolicyItem, PaymentMethod, RenewalQuote
from app.schemas.policy import ExclusionItem, PaymentMethodCreate, PolicyCreate, PolicyUpdate, PolicyItemCreate, PolicyItemUpdate
from app.exceptions import NotFoundError, BadRequestError


class PolicyService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def list_policies(self, user_id: str, status: str = None) -> list[Policy]:
        query = select(Policy).options(
            selectinload(Policy.items)
        ).where(Policy.user_id == user_id)

        if status:
            query = query.where(Policy.status == status)

        query = query.order_by(Policy.end_date.desc())
        result = await self.db.execute(query)
        policies = list(result.scalars().all())

        today = date.today()
        for p in policies:
            p.days_remaining = (p.end_date - today).days if p.end_date >= today else 0
            if p.vehicle:
                p.vehicle_plate = p.vehicle.plate_number
                p.vehicle_brand = p.vehicle.brand
                p.vehicle_model = p.vehicle.model

        return policies

    async def get_policy_detail(self, user_id: str, policy_id: str) -> Policy:
        result = await self.db.execute(
            select(Policy).options(
                selectinload(Policy.items)
            ).where(and_(Policy.id == policy_id, Policy.user_id == user_id))
        )
        policy = result.scalar_one_or_none()
        if not policy:
            raise NotFoundError("保單不存在")

        today = date.today()
        policy.days_remaining = (policy.end_date - today).days if policy.end_date >= today else 0
        return policy

    async def get_exclusions(self, user_id: str, policy_id: str) -> list[ExclusionItem]:
        policy = await self.get_policy_detail(user_id, policy_id)
        exclusions = []
        for item in policy.items:
            if item.exclusions:
                try:
                    items_data = json.loads(item.exclusions)
                    for exc in items_data:
                        exclusions.append(ExclusionItem(
                            item_name=item.item_name,
                            category=exc.get("category", "一般不賠"),
                            description=exc.get("description", ""),
                            scenario=exc.get("scenario", ""),
                        ))
                except json.JSONDecodeError:
                    pass
        return exclusions

    async def has_excess_liability(self, user_id: str, policy_id: str) -> bool:
        """檢查保單是否含超額責任險"""
        policy = await self.get_policy_detail(user_id, policy_id)
        return any(
            "超額" in item.item_name and item.is_active
            for item in policy.items
        )

    # Renewal quotes
    async def list_renewal_quotes(self, policy_id: str) -> list[RenewalQuote]:
        result = await self.db.execute(
            select(RenewalQuote).where(RenewalQuote.policy_id == policy_id)
            .order_by(RenewalQuote.quoted_premium)
        )
        return list(result.scalars().all())

    async def select_quote(self, user_id: str, quote_id: str) -> RenewalQuote:
        result = await self.db.execute(
            select(RenewalQuote).where(RenewalQuote.id == quote_id)
        )
        quote = result.scalar_one_or_none()
        if not quote:
            raise NotFoundError("報價不存在")

        # 取消同一保單其他選擇
        all_quotes = await self.db.execute(
            select(RenewalQuote).where(RenewalQuote.policy_id == quote.policy_id)
        )
        for q in all_quotes.scalars().all():
            q.is_selected = (q.id == quote_id)

        await self.db.flush()
        return quote

    # Payment methods
    async def list_payment_methods(self, user_id: str) -> list[PaymentMethod]:
        result = await self.db.execute(
            select(PaymentMethod).where(
                and_(PaymentMethod.user_id == user_id, PaymentMethod.is_active == True)
            )
        )
        return list(result.scalars().all())

    async def create_payment_method(self, user_id: str, data: PaymentMethodCreate) -> PaymentMethod:
        if data.is_default:
            existing = await self.db.execute(
                select(PaymentMethod).where(
                    and_(PaymentMethod.user_id == user_id, PaymentMethod.is_default == True)
                )
            )
            for pm in existing.scalars().all():
                pm.is_default = False

        method = PaymentMethod(user_id=user_id, **data.model_dump())
        self.db.add(method)
        await self.db.flush()
        return method

    async def delete_payment_method(self, user_id: str, method_id: str) -> None:
        result = await self.db.execute(
            select(PaymentMethod).where(
                and_(PaymentMethod.id == method_id, PaymentMethod.user_id == user_id)
            )
        )
        method = result.scalar_one_or_none()
        if not method:
            raise NotFoundError("付款方式不存在")
        method.is_active = False
        await self.db.flush()

    # ===== Policy CRUD =====

    async def create_policy(self, user_id: str, data: PolicyCreate) -> Policy:
        # 檢查保單號碼是否重複
        existing = await self.db.execute(
            select(Policy).where(Policy.policy_number == data.policy_number)
        )
        if existing.scalar_one_or_none():
            raise BadRequestError(f"保單號碼 {data.policy_number} 已存在")

        policy = Policy(
            user_id=user_id,
            vehicle_id=data.vehicle_id,
            insurer_name=data.insurer_name,
            policy_number=data.policy_number,
            status=data.status,
            start_date=data.start_date,
            end_date=data.end_date,
            total_premium=data.total_premium,
            document_url=data.document_url,
        )
        self.db.add(policy)
        await self.db.flush()

        # 建立保障項目
        for item_data in data.items:
            item = PolicyItem(
                policy_id=policy.id,
                item_name=item_data.item_name,
                coverage_limit=item_data.coverage_limit,
                deductible=item_data.deductible,
                premium=item_data.premium,
                is_active=item_data.is_active,
                description=item_data.description,
                exclusions=item_data.exclusions,
            )
            self.db.add(item)

        await self.db.flush()
        # 重新載入含 items
        return await self.get_policy_detail(user_id, policy.id)

    async def update_policy(self, user_id: str, policy_id: str, data: PolicyUpdate) -> Policy:
        policy = await self.get_policy_detail(user_id, policy_id)
        update_data = data.model_dump(exclude_unset=True)

        # 檢查保單號碼唯一性
        if "policy_number" in update_data and update_data["policy_number"] != policy.policy_number:
            existing = await self.db.execute(
                select(Policy).where(Policy.policy_number == update_data["policy_number"])
            )
            if existing.scalar_one_or_none():
                raise BadRequestError(f"保單號碼 {update_data['policy_number']} 已存在")

        for key, value in update_data.items():
            setattr(policy, key, value)
        await self.db.flush()
        return policy

    async def delete_policy(self, user_id: str, policy_id: str) -> None:
        policy = await self.get_policy_detail(user_id, policy_id)
        # 刪除關聯的保障項目
        for item in policy.items:
            await self.db.delete(item)
        await self.db.delete(policy)
        await self.db.flush()

    # ===== PolicyItem CRUD =====

    async def add_policy_item(self, user_id: str, policy_id: str, data: PolicyItemCreate) -> PolicyItem:
        # 確認保單屬於該用戶
        await self.get_policy_detail(user_id, policy_id)
        item = PolicyItem(
            policy_id=policy_id,
            item_name=data.item_name,
            coverage_limit=data.coverage_limit,
            deductible=data.deductible,
            premium=data.premium,
            is_active=data.is_active,
            description=data.description,
            exclusions=data.exclusions,
        )
        self.db.add(item)
        await self.db.flush()
        return item

    async def update_policy_item(self, user_id: str, policy_id: str, item_id: str, data: PolicyItemUpdate) -> PolicyItem:
        await self.get_policy_detail(user_id, policy_id)
        result = await self.db.execute(
            select(PolicyItem).where(
                and_(PolicyItem.id == item_id, PolicyItem.policy_id == policy_id)
            )
        )
        item = result.scalar_one_or_none()
        if not item:
            raise NotFoundError("保障項目不存在")

        update_data = data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(item, key, value)
        await self.db.flush()
        return item

    async def delete_policy_item(self, user_id: str, policy_id: str, item_id: str) -> None:
        await self.get_policy_detail(user_id, policy_id)
        result = await self.db.execute(
            select(PolicyItem).where(
                and_(PolicyItem.id == item_id, PolicyItem.policy_id == policy_id)
            )
        )
        item = result.scalar_one_or_none()
        if not item:
            raise NotFoundError("保障項目不存在")
        await self.db.delete(item)
        await self.db.flush()

from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, update
from app.models.notification import Notification
from app.core.push import push_service
from app.exceptions import NotFoundError


class NotificationService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_notification(
        self,
        user_id: str,
        title: str,
        body: str,
        notification_type: str,
        reference_type: str = None,
        reference_id: str = None,
        channel: str = "in_app",
    ) -> Notification:
        notification = Notification(
            user_id=user_id,
            title=title,
            body=body,
            notification_type=notification_type,
            reference_type=reference_type,
            reference_id=reference_id,
            channel=channel,
        )
        self.db.add(notification)
        await self.db.flush()

        if channel in ("push", "in_app"):
            await push_service.send(
                user_id=user_id,
                title=title,
                body=body,
                data={"type": notification_type, "ref_type": reference_type, "ref_id": reference_id},
            )

        return notification

    async def list_notifications(
        self, user_id: str, unread_only: bool = False, page: int = 1, per_page: int = 20
    ) -> tuple[list[Notification], int]:
        query = select(Notification).where(Notification.user_id == user_id)
        if unread_only:
            query = query.where(Notification.is_read == False)
        query = query.order_by(Notification.created_at.desc())

        # Count
        from sqlalchemy import func
        count_query = select(func.count()).select_from(
            query.subquery()
        )
        total = (await self.db.execute(count_query)).scalar() or 0

        # Paginate
        query = query.offset((page - 1) * per_page).limit(per_page)
        result = await self.db.execute(query)
        return list(result.scalars().all()), total

    async def get_unread_count(self, user_id: str) -> int:
        from sqlalchemy import func
        result = await self.db.execute(
            select(func.count()).where(
                and_(Notification.user_id == user_id, Notification.is_read == False)
            )
        )
        return result.scalar() or 0

    async def mark_read(self, user_id: str, notification_id: str) -> None:
        result = await self.db.execute(
            select(Notification).where(
                and_(Notification.id == notification_id, Notification.user_id == user_id)
            )
        )
        notification = result.scalar_one_or_none()
        if not notification:
            raise NotFoundError("通知不存在")
        notification.is_read = True
        notification.read_at = datetime.now(timezone.utc)

    async def mark_all_read(self, user_id: str) -> int:
        result = await self.db.execute(
            select(Notification).where(
                and_(Notification.user_id == user_id, Notification.is_read == False)
            )
        )
        count = 0
        for n in result.scalars().all():
            n.is_read = True
            n.read_at = datetime.now(timezone.utc)
            count += 1
        return count

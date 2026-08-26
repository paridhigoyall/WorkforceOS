from __future__ import annotations

from typing import List, Optional
from uuid import UUID
from sqlalchemy import select, func, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.notification import Notification, NotificationType


class NotificationRepository:
    """Async repository for Notification database operations."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def create(
        self,
        user_id: UUID,
        title: str,
        message: str,
        type: NotificationType = NotificationType.INFO,
        link: Optional[str] = None,
    ) -> Notification:
        """Create and persist a new in-app notification."""
        notif = Notification(
            user_id=user_id,
            title=title,
            message=message,
            type=type,
            link=link,
            is_read=False,
        )
        self.db.add(notif)
        await self.db.flush()
        return notif

    async def get_by_id(self, notification_id: UUID) -> Optional[Notification]:
        """Fetch single notification by ID."""
        stmt = select(Notification).where(Notification.id == notification_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def list_by_user(
        self,
        user_id: UUID,
        limit: int = 50,
        offset: int = 0,
        unread_only: bool = False,
        type_filter: Optional[NotificationType] = None,
    ) -> List[Notification]:
        """Query paginated user notifications sorted by newest first."""
        stmt = (
            select(Notification)
            .where(Notification.user_id == user_id)
            .order_by(Notification.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        if unread_only:
            stmt = stmt.where(Notification.is_read == False)  # noqa: E712
        if type_filter:
            stmt = stmt.where(Notification.type == type_filter)

        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def get_unread_count(self, user_id: UUID) -> int:
        """Count unacknowledged notifications for a user."""
        stmt = (
            select(func.count(Notification.id))
            .where(Notification.user_id == user_id, Notification.is_read == False)  # noqa: E712
        )
        result = await self.db.execute(stmt)
        return result.scalar_one() or 0

    async def mark_as_read(self, notification_id: UUID, user_id: UUID) -> Optional[Notification]:
        """Mark single notification as read for a specific user."""
        stmt = select(Notification).where(
            Notification.id == notification_id,
            Notification.user_id == user_id,
        )
        result = await self.db.execute(stmt)
        notif = result.scalar_one_or_none()
        if notif:
            notif.is_read = True
            await self.db.flush()
        return notif

    async def mark_all_as_read(self, user_id: UUID) -> int:
        """Mark all notifications as read for a given user."""
        stmt = (
            update(Notification)
            .where(Notification.user_id == user_id, Notification.is_read == False)  # noqa: E712
            .values(is_read=True)
        )
        result = await self.db.execute(stmt)
        await self.db.flush()
        return result.rowcount or 0

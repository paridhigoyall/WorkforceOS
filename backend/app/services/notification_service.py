from __future__ import annotations

from typing import List, Optional
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.notification import Notification, NotificationType
from app.repositories.notification_repository import NotificationRepository
from app.schemas.notification import NotificationResponse, NotificationUnreadCountResponse


class NotificationService:
    """Business logic engine for user alerts and in-app notifications."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.repo = NotificationRepository(db)

    async def send_notification(
        self,
        user_id: UUID,
        title: str,
        message: str,
        type: NotificationType = NotificationType.INFO,
        link: Optional[str] = None,
    ) -> NotificationResponse:
        """Create and dispatch a notification to a specific user."""
        notif = await self.repo.create(
            user_id=user_id,
            title=title,
            message=message,
            type=type,
            link=link,
        )
        return NotificationResponse.model_validate(notif)

    async def get_user_notifications(
        self,
        user_id: UUID,
        limit: int = 50,
        offset: int = 0,
        unread_only: bool = False,
        type_filter: Optional[NotificationType] = None,
    ) -> List[NotificationResponse]:
        """Fetch notifications list for current user."""
        records = await self.repo.list_by_user(
            user_id=user_id,
            limit=limit,
            offset=offset,
            unread_only=unread_only,
            type_filter=type_filter,
        )
        return [NotificationResponse.model_validate(r) for r in records]

    async def get_unread_count(self, user_id: UUID) -> NotificationUnreadCountResponse:
        """Fetch count of unread notifications."""
        count = await self.repo.get_unread_count(user_id)
        return NotificationUnreadCountResponse(unread_count=count)

    async def mark_read(self, notification_id: UUID, user_id: UUID) -> NotificationResponse:
        """Mark single notification as read."""
        notif = await self.repo.mark_as_read(notification_id, user_id)
        if not notif:
            raise ValueError(f"Notification '{notification_id}' not found.")
        await self.db.commit()
        return NotificationResponse.model_validate(notif)

    async def mark_all_read(self, user_id: UUID) -> int:
        """Mark all notifications as read for current user."""
        count = await self.repo.mark_all_as_read(user_id)
        await self.db.commit()
        return count

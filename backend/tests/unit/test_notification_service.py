from __future__ import annotations

import pytest
from uuid import uuid4
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.models.notification import Notification, NotificationType
from app.services.notification_service import NotificationService


class TestNotificationService:
    async def test_notification_lifecycle(
        self,
        db_session: AsyncSession,
        staff_user: User,
    ):
        service = NotificationService(db_session)

        # 1. Send notifications
        notif1 = await service.send_notification(
            user_id=staff_user.id,
            title="Leave Approved",
            message="Your leave request has been approved.",
            type=NotificationType.LEAVE,
        )
        notif2 = await service.send_notification(
            user_id=staff_user.id,
            title="Payslip Generated",
            message="Your payslip is available.",
            type=NotificationType.PAYROLL,
        )

        assert notif1.id is not None
        assert notif1.is_read is False

        # 2. Check unread count
        unread_res = await service.get_unread_count(staff_user.id)
        assert unread_res.unread_count >= 2

        # 3. Mark single as read
        marked = await service.mark_read(notif1.id, staff_user.id)
        assert marked.is_read is True

        # 4. Check updated unread count
        unread_after = await service.get_unread_count(staff_user.id)
        assert unread_after.unread_count == unread_res.unread_count - 1

        # 5. Mark all as read
        await service.mark_all_read(staff_user.id)
        cleared = await service.get_unread_count(staff_user.id)
        assert cleared.unread_count == 0

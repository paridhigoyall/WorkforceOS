from __future__ import annotations

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.models.notification import Notification, NotificationType


class TestNotificationsAPI:
    async def test_notifications_lifecycle_api(
        self,
        client: AsyncClient,
        staff_headers: dict[str, str],
        staff_user: User,
        db_session: AsyncSession,
    ):
        # 1. Create a notification directly in db for user
        notif = Notification(
            user_id=staff_user.id,
            title="System Alert",
            message="Maintenance tonight",
            type=NotificationType.INFO,
            is_read=False,
        )
        db_session.add(notif)
        await db_session.flush()

        # 2. Get unread count
        count_res = await client.get("/api/notifications/unread-count", headers=staff_headers)
        assert count_res.status_code == 200
        assert count_res.json()["unread_count"] >= 1

        # 3. List notifications
        list_res = await client.get("/api/notifications/", headers=staff_headers)
        assert list_res.status_code == 200
        assert len(list_res.json()) >= 1

        # 4. Mark single as read
        read_res = await client.put(f"/api/notifications/{notif.id}/read", headers=staff_headers)
        assert read_res.status_code == 200
        assert read_res.json()["is_read"] is True

        # 5. Mark all as read
        all_res = await client.put("/api/notifications/read-all", headers=staff_headers)
        assert all_res.status_code == 200
        assert "marked_read_count" in all_res.json()

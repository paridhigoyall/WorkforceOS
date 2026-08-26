from __future__ import annotations

from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field

from app.models.notification import NotificationType


class NotificationCreate(BaseModel):
    """Internal schema for creating a notification."""

    user_id: UUID
    title: str = Field(..., max_length=255)
    message: str
    type: NotificationType = NotificationType.INFO
    link: str | None = None


class NotificationResponse(BaseModel):
    """Public schema for a notification."""

    id: UUID
    user_id: UUID
    title: str
    message: str
    type: NotificationType
    link: str | None = None
    is_read: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class NotificationUnreadCountResponse(BaseModel):
    """Fast unread count response."""

    unread_count: int

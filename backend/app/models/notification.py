from __future__ import annotations

import enum
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import Boolean, Enum, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.models.user import User


class NotificationType(str, enum.Enum):
    INFO = "info"
    SUCCESS = "success"
    WARNING = "warning"
    ERROR = "error"
    LEAVE = "leave"
    ATTENDANCE = "attendance"
    PAYROLL = "payroll"


class Notification(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """In-app user notification entity."""

    __tablename__ = "notifications"

    user_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Recipient user UUID",
    )
    title: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        comment="Notification headline",
    )
    message: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment="Notification body text",
    )
    type: Mapped[NotificationType] = mapped_column(
        Enum(NotificationType, native_enum=False, length=30),
        nullable=False,
        default=NotificationType.INFO,
        comment="Category type for UI rendering and filtering",
    )
    link: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
        comment="Optional internal link or route URL",
    )
    is_read: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        index=True,
        comment="Whether the notification has been acknowledged",
    )

    # Relationships
    user: Mapped[User] = relationship("User", back_populates="notifications")

    def __repr__(self) -> str:
        return f"<Notification id={self.id} user_id={self.user_id} title={self.title!r} is_read={self.is_read}>"

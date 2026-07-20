from __future__ import annotations

import uuid
from typing import TYPE_CHECKING, Any, Dict, Optional
from uuid import UUID

from sqlalchemy import String, Uuid, ForeignKey
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, UUIDPrimaryKeyMixin, TimestampMixin

if TYPE_CHECKING:
    from app.models.user import User


class AuditLog(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """
    Immutable audit trail of all significant write operations.
    Stores the operator (user), the action performed,
    the target entity type and ID, and a JSONB payload of change details.
    
    Note: No SoftDeleteMixin — audit logs are permanent records.
    """
    __tablename__ = "audit_logs"

    # Operator (admin/hr performing the action)
    user_id: Mapped[UUID] = mapped_column(
        Uuid,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="UUID of the user who triggered this audit event"
    )

    # Action label (e.g. ONBOARD_EMPLOYEE, UPDATE_EMPLOYEE, DELETE_DEPARTMENT)
    action: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,
        comment="Action identifier describing the operation performed"
    )

    # Target entity type (e.g. 'employees', 'departments')
    target_type: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,
        comment="Type/table of the entity affected by this action"
    )

    # Target entity UUID
    target_id: Mapped[UUID] = mapped_column(
        Uuid,
        nullable=False,
        index=True,
        comment="UUID of the specific entity affected by this action"
    )

    # JSONB payload — stores diffs, metadata, and contextual details
    details: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSONB,
        nullable=True,
        default=None,
        comment="Arbitrary JSON payload containing change details and metadata"
    )

    # Relationship back to the operator User
    user: Mapped["User"] = relationship(
        "User",
        back_populates="audit_logs"
    )

    def __repr__(self) -> str:
        return (
            f"<AuditLog action={self.action!r} "
            f"target_type={self.target_type!r} "
            f"target_id={self.target_id} "
            f"user_id={self.user_id}>"
        )

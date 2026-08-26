from __future__ import annotations

import enum
import uuid
from typing import TYPE_CHECKING, List

from sqlalchemy import Boolean, Enum, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, SoftDeleteMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.models.employee import Employee
    from app.models.audit_log import AuditLog
    from app.models.notification import Notification

class UserRole(str, enum.Enum):
    ADMIN = "admin"
    HR = "hr"
    STAFF = "staff"

class User(Base, UUIDPrimaryKeyMixin, TimestampMixin, SoftDeleteMixin):
    """User account model.

    * ``id`` – UUID primary key (provided by ``UUIDPrimaryKeyMixin``).
    * ``email`` – unique, required.
    * ``hashed_password`` – BCrypt hash stored.
    * ``role`` – enum controlling RBAC.
    * ``is_mfa_enabled`` – boolean flag indicating TOTP 2FA is active.
    * ``mfa_secret`` – base32 secret for RFC 6238 TOTP verification.
    * ``employee`` – optional one‑to‑one relationship to :class:`Employee`.
    """

    __tablename__ = "users"

    email: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        nullable=False,
        index=True,
        comment="User login e‑mail address",
    )
    hashed_password: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        comment="BCrypt hashed password",
    )
    role: Mapped[UserRole] = mapped_column(
        Enum(UserRole, native_enum=False, length=20),
        nullable=False,
        default=UserRole.STAFF,
        comment="User role for RBAC",
    )
    is_mfa_enabled: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        comment="Whether MFA/TOTP is required on login",
    )
    mfa_secret: Mapped[str | None] = mapped_column(
        String(64),
        nullable=True,
        comment="Base32 TOTP secret key for MFA",
    )

    # One‑to‑one relationship to Employee (uselist=False enforces 1‑1)
    employee: Mapped[Employee | None] = relationship(
        "Employee",
        back_populates="user",
        uselist=False,
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

    # One-to-many relationship to AuditLog
    audit_logs: Mapped[List[AuditLog]] = relationship(
        "AuditLog",
        back_populates="user",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

    # One-to-many relationship to Notification
    notifications: Mapped[List[Notification]] = relationship(
        "Notification",
        back_populates="user",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

    def __repr__(self) -> str:
        return f"<User id={self.id} email={self.email!r} role={self.role}>"

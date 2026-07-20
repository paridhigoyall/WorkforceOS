"""
Leave database models.

Follows the project's SQLAlchemy conventions:
  - Inherits from Base, UUIDPrimaryKeyMixin, and TimestampMixin
  - Enums map native_enum=False with length=20 to ensure cross-DB compatibility
  - Custom indexes defined for employee_id, status, and start_date
  - LeaveBalance is a separate model to allow extensible future policy changes
    (e.g., per-policy accrual, carry-forward, multi-year tracking)
"""
from __future__ import annotations

import enum
from datetime import date, datetime
from typing import TYPE_CHECKING, Optional
from uuid import UUID

from sqlalchemy import Enum, ForeignKey, Date, DateTime, Integer, String, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.models.employee import Employee
    from app.models.user import User


class LeaveType(str, enum.Enum):
    CASUAL = "Casual"
    SICK = "Sick"
    EARNED = "Earned"
    UNPAID = "Unpaid"


class LeaveStatus(str, enum.Enum):
    PENDING = "Pending"
    APPROVED = "Approved"
    REJECTED = "Rejected"
    CANCELLED = "Cancelled"


class LeaveRequest(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """
    SQLAlchemy model representing an Employee's leave request.

    Inherits UUIDPrimaryKeyMixin (id) and TimestampMixin (created_at, updated_at).
    Indexed on employee_id, status, and start_date for efficient filtering.
    """

    __tablename__ = "leave_requests"

    employee_id: Mapped[UUID] = mapped_column(
        Uuid,
        ForeignKey("employees.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Foreign key referencing the associated employee"
    )

    leave_type: Mapped[LeaveType] = mapped_column(
        Enum(LeaveType, native_enum=False, length=20),
        nullable=False,
        comment="Type of leave requested (e.g. Casual, Sick, Earned, Unpaid)"
    )

    start_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
        index=True,
        comment="Start date of the leave period"
    )

    end_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
        comment="End date of the leave period"
    )

    total_days: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        comment="Total number of calendar days in the leave request"
    )

    reason: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        comment="Reason provided for the leave application"
    )

    status: Mapped[LeaveStatus] = mapped_column(
        Enum(LeaveStatus, native_enum=False, length=20),
        nullable=False,
        default=LeaveStatus.PENDING,
        index=True,
        comment="Current validation status of the request"
    )

    approved_by: Mapped[Optional[UUID]] = mapped_column(
        Uuid,
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
        comment="Foreign key referencing the user/admin who approved/rejected the request"
    )

    approved_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="Timestamp of when the request status was processed"
    )

    # Relationships
    employee: Mapped["Employee"] = relationship(
        "Employee",
        back_populates="leave_requests"
    )

    approver: Mapped[Optional["User"]] = relationship(
        "User",
        foreign_keys=[approved_by]
    )

    def __repr__(self) -> str:
        return (
            f"<LeaveRequest id={self.id} "
            f"employee_id={self.employee_id} "
            f"type={self.leave_type} "
            f"status={self.status}>"
        )


class LeaveBalance(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """
    Tracks per-employee, per-leave-type balance allocation and usage.

    Designed for extensibility — future policies can add new LeaveType entries
    or introduce carry-forward/accrual logic without schema changes.

    Inherits UUIDPrimaryKeyMixin (id) and TimestampMixin (created_at, updated_at).
    """

    __tablename__ = "leave_balances"

    employee_id: Mapped[UUID] = mapped_column(
        Uuid,
        ForeignKey("employees.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Foreign key referencing the associated employee"
    )

    leave_type: Mapped[LeaveType] = mapped_column(
        Enum(LeaveType, native_enum=False, length=20),
        nullable=False,
        comment="The type of leave this balance entry tracks"
    )

    year: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        comment="The calendar year this balance applies to"
    )

    allocated_days: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        comment="Total days allocated for this leave type in the given year"
    )

    used_days: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        comment="Total days consumed by approved leave requests"
    )

    # Relationships
    employee: Mapped["Employee"] = relationship(
        "Employee",
        back_populates="leave_balances"
    )

    def __repr__(self) -> str:
        return (
            f"<LeaveBalance id={self.id} "
            f"employee_id={self.employee_id} "
            f"type={self.leave_type} "
            f"year={self.year} "
            f"allocated={self.allocated_days} used={self.used_days}>"
        )

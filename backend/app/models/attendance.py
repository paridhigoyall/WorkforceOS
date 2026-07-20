import enum
import uuid
from datetime import date, datetime
from decimal import Decimal
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import Enum, ForeignKey, Date, DateTime, Numeric, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.models.employee import Employee


class AttendanceStatus(str, enum.Enum):
    PRESENT = "Present"
    ABSENT = "Absent"
    HALF_DAY = "Half-Day"
    LATE = "Late"


class Attendance(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """
    SQLAlchemy model representing an Employee's daily attendance record.
    
    Inherits UUIDPrimaryKeyMixin (id) and TimestampMixin (created_at, updated_at).
    """
    __tablename__ = "attendances"

    employee_id: Mapped[UUID] = mapped_column(
        Uuid,
        ForeignKey("employees.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Foreign key referencing the associated employee"
    )

    attendance_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
        index=True,
        comment="The date of this attendance record"
    )

    check_in_time: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        comment="Timestamp when the employee checked in"
    )

    check_out_time: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="Timestamp when the employee checked out"
    )

    total_hours: Mapped[Decimal] = mapped_column(
        Numeric(5, 2),
        nullable=False,
        default=Decimal("0.00"),
        comment="Total hours worked for the day"
    )

    attendance_status: Mapped[AttendanceStatus] = mapped_column(
        Enum(AttendanceStatus, native_enum=False, length=20),
        nullable=False,
        comment="Status for the day (e.g., Present, Absent, Half-Day, Late)"
    )

    # Relationship back to Employee
    employee: Mapped["Employee"] = relationship(
        "Employee",
        back_populates="attendances"
    )

    def __repr__(self) -> str:
        return f"<Attendance id={self.id} employee_id={self.employee_id} date={self.attendance_date} status={self.attendance_status}>"

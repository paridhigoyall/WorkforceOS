import uuid
from datetime import date
from decimal import Decimal
from typing import TYPE_CHECKING, List
from uuid import UUID
from sqlalchemy import String, Date, Numeric, ForeignKey, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, SoftDeleteMixin

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.department import Department
    from app.models.attendance import Attendance
    from app.models.leave import LeaveRequest, LeaveBalance


class Employee(Base, TimestampMixin, SoftDeleteMixin):
    """
    SQLAlchemy model representing an Employee.
    
    Inherits TimestampMixin (created_at, updated_at) and SoftDeleteMixin (is_deleted, deleted_at).
    """
    __tablename__ = "employees"

    id: Mapped[UUID] = mapped_column(
        Uuid,
        primary_key=True,
        default=uuid.uuid4,
        index=True,
        nullable=False,
        comment="Unique identifier for the employee"
    )
    
    # 1-to-1 Relationship with User
    user_id: Mapped[UUID] = mapped_column(
        Uuid,
        ForeignKey("users.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
        index=True,
        comment="Foreign key referencing the associated user account"
    )
    
    # Many-to-1 Relationship with Department
    department_id: Mapped[UUID | None] = mapped_column(
        Uuid,
        ForeignKey("departments.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
        comment="Foreign key referencing the associated department"
    )
    
    hire_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
        comment="The date the employee was officially hired"
    )
    
    phone: Mapped[str | None] = mapped_column(
        String(20),
        nullable=True,
        comment="Contact phone number of the employee"
    )
    
    base_salary: Mapped[Decimal] = mapped_column(
        Numeric(12, 2),
        nullable=False,
        default=Decimal("0.00"),
        comment="Monthly base salary of the employee"
    )

    # Relationships
    user: Mapped["User"] = relationship(
        "User",
        back_populates="employee"
    )
    
    department: Mapped["Department | None"] = relationship(
        "Department",
        back_populates="employees"
    )
    
    attendances: Mapped[List["Attendance"]] = relationship(
        "Attendance",
        back_populates="employee",
        cascade="all, delete-orphan",
        passive_deletes=True
    )

    leave_requests: Mapped[List["LeaveRequest"]] = relationship(
        "LeaveRequest",
        back_populates="employee",
        cascade="all, delete-orphan",
        passive_deletes=True
    )

    leave_balances: Mapped[List["LeaveBalance"]] = relationship(
        "LeaveBalance",
        back_populates="employee",
        cascade="all, delete-orphan",
        passive_deletes=True
    )

    def __repr__(self) -> str:
        return f"<Employee id={self.id} user_id={self.user_id} department_id={self.department_id}>"

from __future__ import annotations

import enum
from datetime import datetime
from typing import TYPE_CHECKING, List, Optional
from uuid import UUID

from sqlalchemy import String, Numeric, Enum as SQLEnum, ForeignKey, Integer, Uuid, UniqueConstraint, DateTime

from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, UUIDPrimaryKeyMixin, TimestampMixin

if TYPE_CHECKING:
    from app.models.employee import Employee


class PayrollPeriodStatus(str, enum.Enum):
    DRAFT = "DRAFT"
    PROCESSING = "PROCESSING"
    APPROVED = "APPROVED"
    PAID = "PAID"


class PayrollRecordStatus(str, enum.Enum):
    PENDING = "PENDING"
    PAID = "PAID"


class PayrollPeriod(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """
    Monthly payroll processing batch.
    Groups individual employee payroll records for a specific year & month.
    """
    __tablename__ = "payroll_periods"
    __table_args__ = (
        UniqueConstraint("year", "month", name="uq_payroll_period_year_month"),
    )

    year: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        index=True,
        comment="Payroll calendar year (e.g. 2026)"
    )

    month: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        index=True,
        comment="Payroll month (1-12)"
    )

    status: Mapped[PayrollPeriodStatus] = mapped_column(
        SQLEnum(PayrollPeriodStatus),
        nullable=False,
        default=PayrollPeriodStatus.DRAFT,
        index=True
    )

    total_gross_pay: Mapped[float] = mapped_column(
        Numeric(12, 2),
        nullable=False,
        default=0.00
    )

    total_deductions: Mapped[float] = mapped_column(
        Numeric(12, 2),
        nullable=False,
        default=0.00
    )

    total_net_pay: Mapped[float] = mapped_column(
        Numeric(12, 2),
        nullable=False,
        default=0.00
    )

    employee_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0
    )

    approved_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        default=None
    )


    # Relationships
    records: Mapped[List["PayrollRecord"]] = relationship(
        "PayrollRecord",
        back_populates="payroll_period",
        cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<PayrollPeriod year={self.year} month={self.month} status={self.status.value}>"


class PayrollRecord(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """
    Individual payslip item for an employee in a specific payroll batch.
    """
    __tablename__ = "payroll_records"
    __table_args__ = (
        UniqueConstraint("payroll_period_id", "employee_id", name="uq_payroll_record_period_employee"),
    )

    payroll_period_id: Mapped[UUID] = mapped_column(
        Uuid,
        ForeignKey("payroll_periods.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    employee_id: Mapped[UUID] = mapped_column(
        Uuid,
        ForeignKey("employees.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    base_salary: Mapped[float] = mapped_column(
        Numeric(10, 2),
        nullable=False,
        default=0.00
    )

    overtime_hours: Mapped[float] = mapped_column(
        Numeric(6, 2),
        nullable=False,
        default=0.00
    )

    overtime_pay: Mapped[float] = mapped_column(
        Numeric(10, 2),
        nullable=False,
        default=0.00
    )

    unpaid_leave_days: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0
    )

    unpaid_leave_deduction: Mapped[float] = mapped_column(
        Numeric(10, 2),
        nullable=False,
        default=0.00
    )

    tax_deduction: Mapped[float] = mapped_column(
        Numeric(10, 2),
        nullable=False,
        default=0.00
    )

    net_pay: Mapped[float] = mapped_column(
        Numeric(10, 2),
        nullable=False,
        default=0.00
    )

    status: Mapped[PayrollRecordStatus] = mapped_column(
        SQLEnum(PayrollRecordStatus),
        nullable=False,
        default=PayrollRecordStatus.PENDING
    )

    # Relationships
    payroll_period: Mapped["PayrollPeriod"] = relationship(
        "PayrollPeriod",
        back_populates="records"
    )

    employee: Mapped["Employee"] = relationship(
        "Employee"
    )

    def __repr__(self) -> str:
        return f"<PayrollRecord employee_id={self.employee_id} net_pay={self.net_pay}>"

from __future__ import annotations

import calendar
from datetime import date, datetime, timezone
from typing import List, Optional
from uuid import UUID

from sqlalchemy import select, func, extract
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.employee import Employee
from app.models.attendance import Attendance
from app.models.leave import LeaveRequest, LeaveType, LeaveStatus
from app.models.audit_log import AuditLog
from app.models.payroll import PayrollPeriod, PayrollPeriodStatus, PayrollRecord, PayrollRecordStatus
from app.repositories.payroll_repository import PayrollRepository
from app.schemas.payroll import (
    PayrollGenerationRequest,
    PayrollPeriodResponse,
    PayrollRecordResponse,
    PayslipDetailResponse
)


class PayrollService:
    """Core business logic engine for payroll generation, calculations, and payslip exports."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.repo = PayrollRepository(db)

    async def generate_monthly_payroll(
        self,
        schema: PayrollGenerationRequest,
        operator_id: UUID
    ) -> PayrollPeriodResponse:
        """
        Generate or recalculate monthly payroll batch for all active employees.
        Integrates overtime hours from Attendance and unpaid leave days from LeaveRequests.
        """
        # Check if period already exists
        existing = await self.repo.get_period_by_year_month(schema.year, schema.month)
        if existing:
            if existing.status == PayrollPeriodStatus.APPROVED or existing.status == PayrollPeriodStatus.PAID:
                raise ValueError(f"Payroll period {schema.year}-{schema.month:02d} is already {existing.status.value} and cannot be regenerated.")
            # Delete old draft records for recalculation
            await self.db.delete(existing)
            await self.db.flush()

        # Fetch active employees
        emp_stmt = (
            select(Employee)
            .where(Employee.is_deleted == False)  # noqa: E712
            .options(selectinload(Employee.user), selectinload(Employee.department))
        )
        res = await self.db.execute(emp_stmt)
        employees = list(res.scalars().all())

        if not employees:
            raise ValueError("No active employees found to generate payroll.")

        # Determine date range for target month
        _, last_day = calendar.monthrange(schema.year, schema.month)
        start_date = date(schema.year, schema.month, 1)
        end_date = date(schema.year, schema.month, last_day)

        period = PayrollPeriod(
            year=schema.year,
            month=schema.month,
            status=PayrollPeriodStatus.DRAFT,
            total_gross_pay=0.00,
            total_deductions=0.00,
            total_net_pay=0.00,
            employee_count=len(employees)
        )

        total_gross = 0.0
        total_deduct = 0.0
        total_net = 0.0

        records: List[PayrollRecord] = []

        for emp in employees:
            base_sal = float(emp.base_salary or 0.0)

            # 1. Calculate Overtime Hours from Attendance in period (hours > 8.0 per day)
            att_stmt = select(Attendance).where(
                Attendance.employee_id == emp.id,
                Attendance.attendance_date >= start_date,
                Attendance.attendance_date <= end_date,
                Attendance.total_hours > 8.0
            )
            att_res = await self.db.execute(att_stmt)
            att_records = list(att_res.scalars().all())
            ot_hours = sum(float(a.total_hours) - 8.0 for a in att_records)

            # Overtime rate: (Base / 160 standard working hours) * 1.5 multiplier
            hourly_rate = base_sal / 160.0 if base_sal > 0 else 0.0
            ot_pay = ot_hours * hourly_rate * 1.5

            # 2. Calculate Unpaid Leave Days in period
            leave_stmt = select(LeaveRequest).where(
                LeaveRequest.employee_id == emp.id,
                LeaveRequest.leave_type == LeaveType.UNPAID,
                LeaveRequest.status == LeaveStatus.APPROVED,
                LeaveRequest.start_date <= end_date,
                LeaveRequest.end_date >= start_date
            )
            leave_res = await self.db.execute(leave_stmt)
            unpaid_leaves = list(leave_res.scalars().all())
            unpaid_days = sum(l.total_days for l in unpaid_leaves)

            # Unpaid daily deduction rate: Base / 22 working days
            daily_rate = base_sal / 22.0 if base_sal > 0 else 0.0
            unpaid_deduction = unpaid_days * daily_rate

            # 3. Calculate Tax Deduction (10% on gross earnings)
            gross_earnings = base_sal + ot_pay
            tax_deduction = gross_earnings * 0.10

            # 4. Net Pay calculation
            total_emp_deductions = unpaid_deduction + tax_deduction
            net_pay = max(0.0, gross_earnings - total_emp_deductions)

            record = PayrollRecord(
                employee_id=emp.id,
                base_salary=round(base_sal, 2),
                overtime_hours=round(ot_hours, 2),
                overtime_pay=round(ot_pay, 2),
                unpaid_leave_days=unpaid_days,
                unpaid_leave_deduction=round(unpaid_deduction, 2),
                tax_deduction=round(tax_deduction, 2),
                net_pay=round(net_pay, 2),
                status=PayrollRecordStatus.PENDING
            )
            records.append(record)

            total_gross += gross_earnings
            total_deduct += total_emp_deductions
            total_net += net_pay

        period.total_gross_pay = round(total_gross, 2)
        period.total_deductions = round(total_deduct, 2)
        period.total_net_pay = round(total_net, 2)
        period.records = records

        self.db.add(period)
        await self.db.flush()

        # Audit log creation
        audit = AuditLog(
            user_id=operator_id,
            action="GENERATE_PAYROLL",
            target_type="payroll_periods",
            target_id=period.id,
            details={
                "year": schema.year,
                "month": schema.month,
                "employee_count": len(employees),
                "total_net_pay": period.total_net_pay
            }
        )
        self.db.add(audit)
        await self.db.commit()

        # Reload complete period with relations
        reloaded = await self.repo.get_period_by_id(period.id)
        return self._to_period_response(reloaded)

    async def get_period(self, period_id: UUID) -> PayrollPeriodResponse:
        """Fetch details of a specific payroll period."""
        period = await self.repo.get_period_by_id(period_id)
        if not period:
            raise ValueError(f"Payroll period '{period_id}' not found.")
        return self._to_period_response(period)

    async def list_periods(self, limit: int = 24, offset: int = 0) -> List[PayrollPeriodResponse]:
        """List historical payroll periods."""
        periods = await self.repo.list_periods(limit=limit, offset=offset)
        return [self._to_period_response(p) for p in periods]

    async def approve_period(self, period_id: UUID, operator_id: UUID) -> PayrollPeriodResponse:
        """Approve a payroll batch and mark records as PAID."""
        period = await self.repo.get_period_by_id(period_id)
        if not period:
            raise ValueError(f"Payroll period '{period_id}' not found.")
        if period.status == PayrollPeriodStatus.APPROVED:
            raise ValueError("Payroll period is already approved.")

        period.status = PayrollPeriodStatus.APPROVED
        period.approved_at = datetime.now(timezone.utc)
        for rec in period.records:
            rec.status = PayrollRecordStatus.PAID

        audit = AuditLog(
            user_id=operator_id,
            action="APPROVE_PAYROLL",
            target_type="payroll_periods",
            target_id=period.id,
            details={"year": period.year, "month": period.month, "total_net_pay": float(period.total_net_pay)}
        )
        self.db.add(audit)
        await self.db.commit()

        reloaded = await self.repo.get_period_by_id(period.id)
        return self._to_period_response(reloaded)

    async def get_payslip(self, record_id: UUID) -> PayslipDetailResponse:
        """Generate comprehensive printable digital payslip."""
        record = await self.repo.get_record_by_id(record_id)
        if not record:
            raise ValueError(f"Payroll record '{record_id}' not found.")

        emp = record.employee
        user_email = emp.user.email if emp and emp.user else None
        dept_name = emp.department.name if emp and emp.department else None

        base_sal = float(record.base_salary)
        ot_pay = float(record.overtime_pay)
        gross = base_sal + ot_pay
        unpaid_ded = float(record.unpaid_leave_deduction)
        tax_ded = float(record.tax_deduction)
        tot_ded = unpaid_ded + tax_ded
        net = float(record.net_pay)

        return PayslipDetailResponse(
            id=record.id,
            period_year=record.payroll_period.year,
            period_month=record.payroll_period.month,
            employee_id=record.employee_id,
            employee_email=user_email,
            department_name=dept_name,
            base_salary=base_sal,
            overtime_hours=float(record.overtime_hours),
            overtime_pay=ot_pay,
            unpaid_leave_days=record.unpaid_leave_days,
            unpaid_leave_deduction=unpaid_ded,
            gross_earnings=gross,
            total_deductions=tot_ded,
            tax_deduction=tax_ded,
            net_pay=net,
            status=record.status,
            generated_at=datetime.now(timezone.utc)
        )

    def _to_period_response(self, period: PayrollPeriod) -> PayrollPeriodResponse:
        """Helper to transform ORM PayrollPeriod into Pydantic schema."""
        rec_responses = []
        if period.records:
            for r in period.records:
                emp = r.employee
                rec_responses.append(
                    PayrollRecordResponse(
                        id=r.id,
                        payroll_period_id=r.payroll_period_id,
                        employee_id=r.employee_id,
                        employee_email=emp.user.email if emp and emp.user else None,
                        department_name=emp.department.name if emp and emp.department else None,
                        base_salary=float(r.base_salary),
                        overtime_hours=float(r.overtime_hours),
                        overtime_pay=float(r.overtime_pay),
                        unpaid_leave_days=r.unpaid_leave_days,
                        unpaid_leave_deduction=float(r.unpaid_leave_deduction),
                        tax_deduction=float(r.tax_deduction),
                        net_pay=float(r.net_pay),
                        status=r.status,
                        created_at=r.created_at
                    )
                )

        return PayrollPeriodResponse(
            id=period.id,
            year=period.year,
            month=period.month,
            status=period.status,
            total_gross_pay=float(period.total_gross_pay),
            total_deductions=float(period.total_deductions),
            total_net_pay=float(period.total_net_pay),
            employee_count=period.employee_count,
            approved_at=period.approved_at,
            created_at=period.created_at,
            records=rec_responses
        )

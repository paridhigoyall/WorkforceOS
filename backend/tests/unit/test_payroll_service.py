from __future__ import annotations

import pytest
from datetime import date, datetime, timezone
from uuid import uuid4
from decimal import Decimal
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.models.employee import Employee
from app.models.attendance import Attendance, AttendanceStatus
from app.models.payroll import PayrollPeriodStatus, PayrollRecordStatus
from app.schemas.payroll import PayrollGenerationRequest
from app.services.payroll_service import PayrollService


class TestPayrollService:
    async def test_generate_payroll_with_overtime_and_deductions(
        self,
        db_session: AsyncSession,
        test_employee: Employee,
        admin_user: User,
    ):
        service = PayrollService(db_session)

        # Add 1 day with 10 hours of attendance (2 hours overtime) in April 2025
        att = Attendance(
            employee_id=test_employee.id,
            attendance_date=date(2025, 4, 15),
            check_in_time=datetime(2025, 4, 15, 8, 0, 0, tzinfo=timezone.utc),
            check_out_time=datetime(2025, 4, 15, 18, 0, 0, tzinfo=timezone.utc),
            total_hours=Decimal("10.00"),
            attendance_status=AttendanceStatus.PRESENT,
        )
        db_session.add(att)
        await db_session.flush()

        schema = PayrollGenerationRequest(year=2025, month=4)
        period = await service.generate_monthly_payroll(schema, operator_id=admin_user.id)

        assert period.id is not None
        assert period.year == 2025
        assert period.month == 4
        assert period.status == PayrollPeriodStatus.DRAFT
        assert len(period.records) >= 1

        rec = next(r for r in period.records if r.employee_id == test_employee.id)
        assert rec.base_salary == 6000.00
        assert rec.overtime_hours == 2.0
        # Overtime rate: (6000/160)*1.5 = 56.25/hr * 2 = 112.50
        assert rec.overtime_pay == 112.50
        assert rec.net_pay > 0

    async def test_approve_payroll_period(
        self,
        db_session: AsyncSession,
        test_employee: Employee,
        admin_user: User,
    ):
        service = PayrollService(db_session)
        schema = PayrollGenerationRequest(year=2025, month=5)
        period = await service.generate_monthly_payroll(schema, operator_id=admin_user.id)

        approved = await service.approve_period(period.id, operator_id=admin_user.id)
        assert approved.status == PayrollPeriodStatus.APPROVED
        assert approved.approved_at is not None

        # Payslip query
        record_id = approved.records[0].id
        payslip = await service.get_payslip(record_id)
        assert payslip.period_year == 2025
        assert payslip.period_month == 5
        assert payslip.net_pay > 0

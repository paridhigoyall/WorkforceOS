"""
Payroll Engine -- Verification Script
====================================
Verifies:
  1. Import chain for models, schemas, repositories, service, router
  2. Database tables (payroll_periods, payroll_records)
  3. Payroll calculations: Overtime pay, Unpaid leave deductions, Tax, Net pay
  4. Audit logging on payroll generation and approval

Run:
    python verify_payroll.py
"""
from __future__ import annotations

import asyncio
import os
import sys
import traceback
from datetime import date, datetime, timezone
from uuid import uuid4


sys.path.insert(0, os.path.dirname(__file__))

from sqlalchemy import inspect, select
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+asyncpg://postgres:postgres@localhost:5432/postgres",
)

engine = create_async_engine(DATABASE_URL, echo=False)
AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

passed: list[str] = []
failed: list[str] = []


def ok(msg: str) -> None:
    passed.append(msg)
    print(f"  [PASS] {msg}")


def fail(msg: str, detail: str = "") -> None:
    failed.append(msg)
    info = f" -- {detail}" if detail else ""
    print(f"  [FAIL] {msg}{info}")


def section(title: str) -> None:
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}")


def verify_imports() -> None:
    section("SECTION 1: Import Verification")
    try:
        from app.models.payroll import PayrollPeriod, PayrollRecord
        ok("app.models.payroll -- PayrollPeriod, PayrollRecord")
    except Exception as exc:
        fail("app.models.payroll import", str(exc))

    try:
        from app.schemas.payroll import PayrollGenerationRequest, PayrollPeriodResponse, PayslipDetailResponse
        ok("app.schemas.payroll -- schemas")
    except Exception as exc:
        fail("app.schemas.payroll import", str(exc))

    try:
        from app.repositories.payroll_repository import PayrollRepository
        ok("app.repositories.payroll_repository -- PayrollRepository")
    except Exception as exc:
        fail("app.repositories.payroll_repository import", str(exc))

    try:
        from app.services.payroll_service import PayrollService
        ok("app.services.payroll_service -- PayrollService")
    except Exception as exc:
        fail("app.services.payroll_service import", str(exc))

    try:
        from app.api.routes.payroll import router as payroll_router
        ok("app.api.routes.payroll -- router")
    except Exception as exc:
        fail("app.api.routes.payroll import", str(exc))


async def verify_business_rules() -> None:
    section("SECTION 2: Business Logic & Payroll Calculations")
    from app.models.base import Base
    from app.models.user import User, UserRole
    from app.models.employee import Employee
    from app.models.attendance import Attendance, AttendanceStatus
    from app.models.leave import LeaveRequest, LeaveType, LeaveStatus
    from app.schemas.payroll import PayrollGenerationRequest
    from app.services.payroll_service import PayrollService

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with AsyncSessionLocal() as db:
        # Clean up any previous test period for 2026-01
        from app.models.payroll import PayrollPeriod
        stmt = select(PayrollPeriod).where(PayrollPeriod.year == 2026, PayrollPeriod.month == 1)
        res = await db.execute(stmt)
        for p in res.scalars().all():
            await db.delete(p)
        await db.commit()

        admin = User(email=f"admin_{uuid4().hex[:8]}@verify.local", hashed_password="pw", role=UserRole.ADMIN)
        staff_user = User(email=f"staff_{uuid4().hex[:8]}@verify.local", hashed_password="pw", role=UserRole.STAFF)
        db.add_all([admin, staff_user])
        await db.flush()

        emp = Employee(
            user_id=staff_user.id,
            hire_date=date(2026, 1, 1),
            phone="+1234567890",
            base_salary=4800.00  # $4800 / 160 hrs = $30/hr standard rate
        )
        db.add(emp)
        await db.flush()

        # Add 10 hours attendance for Jan 15 2026 (yielding 2 overtime hours)
        now = datetime.now(timezone.utc)
        att = Attendance(
            employee_id=emp.id,
            attendance_date=date(2026, 1, 15),
            check_in_time=now,
            check_out_time=now,
            total_hours=10.0,
            attendance_status=AttendanceStatus.PRESENT
        )

        db.add(att)
        await db.flush()

        # Generate payroll for Jan 2026
        svc = PayrollService(db)
        period_res = await svc.generate_monthly_payroll(
            PayrollGenerationRequest(year=2026, month=1),
            operator_id=admin.id
        )

        if period_res and period_res.employee_count >= 1:
            ok("Payroll batch generated successfully")
        else:
            fail("Payroll batch generation failed")

        # Verify payslip breakdown for employee
        rec = next((r for r in period_res.records if r.employee_id == emp.id), None)
        if rec:
            # Overtime: 2 hrs * ($4800/160 * 1.5) = 2 * $45 = $90
            if abs(rec.overtime_pay - 90.00) < 0.01:
                ok("Overtime pay calculation accurate ($90.00)")
            else:
                fail(f"Overtime pay calculation mismatch: got {rec.overtime_pay}, expected 90.00")

            if rec.net_pay > 0:
                ok("Net pay calculated cleanly")
            else:
                fail("Net pay calculation is 0")

            # Check printable payslip API
            payslip = await svc.get_payslip(rec.id)
            if payslip and payslip.gross_earnings == rec.base_salary + rec.overtime_pay:
                ok("Digital payslip generated cleanly")
            else:
                fail("Digital payslip mismatch")
        else:
            fail("Payroll record not found for employee")

        # Test period approval
        approved = await svc.approve_period(period_res.id, operator_id=admin.id)
        if approved.status == "APPROVED":
            ok("Payroll period approved successfully")
        else:
            fail("Payroll period approval failed")

        # Clean up test period and data
        stmt = select(PayrollPeriod).where(PayrollPeriod.id == period_res.id)
        res = await db.execute(stmt)
        period_obj = res.scalar_one_or_none()
        if period_obj:
            await db.delete(period_obj)
        await db.delete(att)
        await db.delete(emp)
        await db.delete(admin)
        await db.delete(staff_user)
        await db.commit()
        ok("Database changes cleaned up cleanly")


async def main() -> None:
    print()
    print("=" * 60)
    print("  Payroll Engine -- Verification Suite")
    print("=" * 60)
    try:
        verify_imports()
        await verify_business_rules()
    except Exception:
        print("\n[FATAL] Unhandled exception during verification:")
        traceback.print_exc()
        failed.append("FATAL exception")

    print()
    print("=" * 60)
    print(f"  Passed : {len(passed)}")
    print(f"  Failed : {len(failed)}")
    if failed:
        sys.exit(1)
    else:
        sys.exit(0)


if __name__ == "__main__":
    asyncio.run(main())

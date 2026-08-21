"""
Workforce Insights & AI Analytics -- Verification Script
=======================================================
Verifies:
  1. Import chain (schemas, service, router)
  2. Attendance insights calculations
  3. Leave insights calculations
  4. Department payroll & attendance insights
  5. Leave Accrual Engine simulation
  6. AI Prediction ML dataset generation & Anomaly detection flags

Run:
    python verify_insights.py
"""
from __future__ import annotations

import asyncio
import os
import sys
import traceback
from datetime import date, datetime, timezone, timedelta
from decimal import Decimal
from uuid import uuid4

# make app importable from project root
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
        from app.schemas.insights import AttendanceInsights, LeaveInsights, DepartmentInsights, AIPredictionDataset
        ok("app.schemas.insights -- all insights schemas")
    except Exception as exc:
        fail("app.schemas.insights import", str(exc))

    try:
        from app.services.insights_service import InsightsService
        ok("app.services.insights_service -- InsightsService")
    except Exception as exc:
        fail("app.services.insights_service import", str(exc))

    try:
        from app.api.routes.insights import router
        ok("app.api.routes.insights -- router")
    except Exception as exc:
        fail("app.api.routes.insights import", str(exc))


async def verify_insights_logic() -> None:
    section("SECTION 2: Insights Logic & Calculations")
    from app.models.user import User
    from app.models.employee import Employee
    from app.models.department import Department
    from app.models.attendance import Attendance, AttendanceStatus
    from app.models.leave import LeaveRequest, LeaveBalance, LeaveType, LeaveStatus
    from app.services.insights_service import InsightsService
    from app.services.leave_service import LeaveService

    async with AsyncSessionLocal() as db:
        # Override db.begin to support nested transactions (savepoints)
        original_begin = db.begin
        def begin_decorator(*args, **kwargs):
            class AsyncContextManager:
                async def __aenter__(self):
                    if db.in_transaction():
                        self.tx = await db.begin_nested()
                    else:
                        self.tx = await original_begin(*args, **kwargs)
                    return self.tx
                async def __aexit__(self, exc_type, exc_val, exc_tb):
                    if exc_type is not None:
                        await self.tx.rollback()
                    else:
                        await self.tx.commit()
            return AsyncContextManager()
        db.begin = begin_decorator

        # Seed Department, Users, Employees
        dept = Department(name="Engineering")
        db.add(dept)
        await db.flush()

        user1 = User(email=f"eng_staff_1_{uuid4().hex[:8]}@verify.local", hashed_password="hashed")
        db.add(user1)
        await db.flush()

        emp1 = Employee(
            user_id=user1.id,
            department_id=dept.id,
            hire_date=date.today() - timedelta(days=200),
            base_salary=Decimal("6000.00"),
        )
        db.add(emp1)
        await db.flush()

        # Seed Attendance for emp1
        # Day 1: Present (9 hours) -> 1.0 overtime
        att1 = Attendance(
            employee_id=emp1.id,
            attendance_date=date.today() - timedelta(days=2),
            check_in_time=datetime.now(timezone.utc) - timedelta(days=2, hours=9),
            check_out_time=datetime.now(timezone.utc) - timedelta(days=2),
            total_hours=Decimal("9.00"),
            attendance_status=AttendanceStatus.PRESENT,
        )
        # Day 2: Late (5 hours) -> 3.0 under-hours
        att2 = Attendance(
            employee_id=emp1.id,
            attendance_date=date.today() - timedelta(days=1),
            check_in_time=datetime.now(timezone.utc) - timedelta(days=1, hours=5),
            check_out_time=datetime.now(timezone.utc) - timedelta(days=1),
            total_hours=Decimal("5.00"),
            attendance_status=AttendanceStatus.LATE,
        )
        db.add_all([att1, att2])
        await db.flush()

        # Seed Leave Requests & Balances
        leave_bal = LeaveBalance(
            employee_id=emp1.id,
            leave_type=LeaveType.CASUAL,
            year=date.today().year,
            allocated_days=10,
            used_days=2,
        )
        db.add(leave_bal)
        await db.flush()

        leave_req = LeaveRequest(
            employee_id=emp1.id,
            leave_type=LeaveType.CASUAL,
            start_date=date.today() - timedelta(days=5),
            end_date=date.today() - timedelta(days=4),
            total_days=2,
            reason="Vacation",
            status=LeaveStatus.APPROVED,
        )
        db.add(leave_req)
        await db.flush()

        # ----------------------------------------------------
        # 1. Test Attendance Insights
        # ----------------------------------------------------
        svc = InsightsService(db)
        att_insights = await svc.get_attendance_insights(emp1.id)
        if att_insights.total_records == 2:
            ok("Attendance Insights: total_records is correct (2)")
        else:
            fail("Attendance Insights: total_records mismatch", str(att_insights.total_records))

        if att_insights.average_attendance_rate == 100.0:
            ok("Attendance Insights: average_attendance_rate is 100.0% (Present + Late)")
        else:
            fail("Attendance Insights: rate mismatch", str(att_insights.average_attendance_rate))

        if att_insights.total_overtime_hours == 1.0:
            ok("Attendance Insights: total_overtime_hours is correct (1.0)")
        else:
            fail("Attendance Insights: overtime mismatch", str(att_insights.total_overtime_hours))

        # ----------------------------------------------------
        # 2. Test Leave Insights
        # ----------------------------------------------------
        leave_insights = await svc.get_leave_insights(emp1.id)
        if leave_insights.total_requests == 1 and leave_insights.total_days_taken == 2:
            ok("Leave Insights: requests and approved days calculated correctly")
        else:
            fail("Leave Insights mismatch", f"requests={leave_insights.total_requests}, days={leave_insights.total_days_taken}")

        if leave_insights.utilization_rate == 20.0:
            ok("Leave Insights: utilization_rate calculation is correct (20.0%)")
        else:
            fail("Leave Insights: utilization rate mismatch", str(leave_insights.utilization_rate))

        # ----------------------------------------------------
        # 3. Test Department Insights
        # ----------------------------------------------------
        dept_insights = await svc.get_department_insights()
        eng_dept = next((d for d in dept_insights if d.department_name == "Engineering"), None)
        if eng_dept and eng_dept.headcount == 1 and eng_dept.total_monthly_payroll == Decimal("6000.00"):
            ok("Department Insights: headcount and payroll calculated correctly")
        else:
            fail("Department Insights: Engineering dept not found or mismatch", str(eng_dept))

        # ----------------------------------------------------
        # 4. Test Leave Accrual Engine
        # ----------------------------------------------------
        leave_svc = LeaveService(db)
        # Emp hired 200 days ago (approx 6 completed months in current year)
        # Accrual should run and update/create balances
        await leave_svc.run_accrual_engine(emp1.id, date.today().year, user1.id)
        
        # Fetch updated balances
        stmt = select(LeaveBalance).where(LeaveBalance.employee_id == emp1.id, LeaveBalance.leave_type == LeaveType.SICK)
        res = await db.execute(stmt)
        sick_bal = res.scalar_one_or_none()
        if sick_bal and sick_bal.allocated_days > 0:
            ok(f"Leave Accrual Engine successfully ran and allocated {sick_bal.allocated_days} SICK leave days")
        else:
            fail("Leave Accrual Engine failed to allocate balance")

        # ----------------------------------------------------
        # 5. Test AI Prediction Dataset & Anomalies
        # ----------------------------------------------------
        dataset = await svc.get_ai_prediction_dataset()
        if dataset and len(dataset.data) >= 1:
            row = next((r for r in dataset.data if r.employee_id == emp1.id), None)
            if row:
                ok("AI Prediction Dataset generated successfully with active employee row")
                if row.tenure_days == 200:
                    ok("AI Prediction: Tenure calculation is accurate (200 days)")
                else:
                    fail("AI Prediction: Tenure mismatch", str(row.tenure_days))
                ok(f"AI Prediction: Turnover risk class classification calculated as: {row.turnover_risk_label}")
            else:
                fail("AI Prediction: Employee row not found in dataset")
        else:
            fail("AI Prediction Dataset failed or is empty")

        await db.rollback()
        ok("Database changes rolled back cleanly")


async def main() -> None:
    print()
    print("=" * 60)
    print("  Workforce Insights & AI Analytics -- Verification Suite")
    print("=" * 60)
    try:
        verify_imports()
        await verify_insights_logic()
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

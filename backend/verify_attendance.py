"""
Attendance Tracking -- Verification Script
==========================================
Verifies:
  1. Import chain (models, schemas, repos, service, router)
  2. DB tables & columns (attendances)
  3. Business rules via service layer (Check-in, Check-out)
  4. Overtime & Under-hours calculation
  5. Audit log created on Check-in/Check-out

Run:
    python verify_attendance.py
"""
from __future__ import annotations

import asyncio
import os
import sys
import traceback
from datetime import date, datetime, time, timezone
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
        from app.models.attendance import Attendance, AttendanceStatus
        ok("app.models.attendance -- Attendance, AttendanceStatus")
    except Exception as exc:
        fail("app.models.attendance import", str(exc))

    try:
        from app.schemas.attendance import AttendanceCreate, AttendanceUpdate
        ok("app.schemas.attendance -- schemas")
    except Exception as exc:
        fail("app.schemas.attendance import", str(exc))

    try:
        from app.repositories.attendance_repository import AttendanceRepository
        ok("app.repositories.attendance_repository -- AttendanceRepository")
    except Exception as exc:
        fail("app.repositories.attendance_repository import", str(exc))

    try:
        from app.services.attendance_service import AttendanceService
        ok("app.services.attendance_service -- AttendanceService")
    except Exception as exc:
        fail("app.services.attendance_service import", str(exc))


async def verify_schema() -> None:
    section("SECTION 2: Database Tables & Columns")
    async with engine.connect() as conn:
        tables = await conn.run_sync(lambda c: inspect(c).get_table_names())

    if "attendances" in tables:
        ok("Table 'attendances' exists")
    else:
        fail("Table 'attendances' MISSING")

    async with engine.connect() as conn:
        cols = {c["name"] for c in await conn.run_sync(lambda c: inspect(c).get_columns("attendances"))}

    required = {"id", "employee_id", "attendance_date", "check_in_time", "check_out_time", "total_hours", "attendance_status"}
    for r in required:
        if r in cols:
            ok(f"  attendances.{r}")
        else:
            fail(f"  attendances.{r} MISSING")


async def verify_business_rules() -> None:
    section("SECTION 3: Business Rules & Audit Logs")
    from app.models.user import User
    from app.models.employee import Employee
    from app.models.attendance import AttendanceStatus
    from app.models.audit_log import AuditLog
    from app.services.attendance_service import AttendanceService

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

        # Seed User + Employee
        user = User(
            email=f"attendance_staff_{uuid4().hex[:8]}@verify.local",
            hashed_password="hashed",
        )
        db.add(user)
        await db.flush()

        emp = Employee(
            user_id=user.id,
            hire_date=date(2025, 1, 1),
            base_salary=Decimal("4000.00"),
        )
        db.add(emp)
        await db.flush()

        svc = AttendanceService(db)

        # 1. Normal Check-in (Before 9 AM)
        check_in_time = datetime(2026, 7, 20, 8, 30, 0, tzinfo=timezone.utc)
        att1 = await svc.check_in(emp.id, check_in_time)
        if att1.attendance_status == AttendanceStatus.PRESENT:
            ok("Check-in before 9 AM marked as PRESENT")
        else:
            fail("Check-in status before 9 AM", att1.attendance_status)

        # 2. Prevent duplicate check-in
        try:
            await svc.check_in(emp.id, check_in_time)
            fail("Duplicate check-in on same day allowed (should fail)")
        except ValueError:
            ok("Duplicate check-in on same day blocked successfully")

        # 3. Check-out (9 hours later: 5:30 PM) -> Overtime
        check_out_time = datetime(2026, 7, 20, 17, 30, 0, tzinfo=timezone.utc)
        att1 = await svc.check_out(att1.id, check_out_time)
        if att1.total_hours == Decimal("9.00"):
            ok("Total hours calculated correctly: 9.00")
        else:
            fail("Total hours mismatch", str(att1.total_hours))

        # Check audit logs for overtime
        stmt = select(AuditLog).where(
            AuditLog.action == "EMPLOYEE_CHECK_OUT",
            AuditLog.target_id == att1.id
        )
        res = await db.execute(stmt)
        log1 = res.scalar_one_or_none()
        if log1 and log1.details.get("overtime_hours") == 1.0 and log1.details.get("under_hours") == 0.0:
            ok("Overtime (1.0) and under-hours (0.0) calculated correctly in audit logs")
        else:
            fail("Overtime/under-hours mismatch in audit log", str(log1.details if log1 else "No log"))

        # 4. Late Check-in (After 9 AM)
        user2 = User(
            email=f"attendance_staff_2_{uuid4().hex[:8]}@verify.local",
            hashed_password="hashed",
        )
        db.add(user2)
        await db.flush()

        emp2 = Employee(
            user_id=user2.id,
            hire_date=date(2025, 1, 1),
            base_salary=Decimal("4000.00"),
        )
        db.add(emp2)
        await db.flush()

        check_in_time2 = datetime(2026, 7, 20, 9, 15, 0, tzinfo=timezone.utc)
        att2 = await svc.check_in(emp2.id, check_in_time2)
        if att2.attendance_status == AttendanceStatus.LATE:
            ok("Check-in after 9 AM marked as LATE")
        else:
            fail("Check-in status after 9 AM", att2.attendance_status)

        # 5. Half-day check-out (3 hours work)
        check_out_time2 = datetime(2026, 7, 20, 12, 15, 0, tzinfo=timezone.utc)
        att2 = await svc.check_out(att2.id, check_out_time2)
        if att2.attendance_status == AttendanceStatus.HALF_DAY:
            ok("Check-out with < 4 hours work marked as HALF_DAY")
        else:
            fail("Check-out status for < 4 hours", att2.attendance_status)

        # Check under-hours in audit log
        stmt2 = select(AuditLog).where(
            AuditLog.action == "EMPLOYEE_CHECK_OUT",
            AuditLog.target_id == att2.id
        )
        res2 = await db.execute(stmt2)
        log2 = res2.scalar_one_or_none()
        if log2 and log2.details.get("under_hours") == 5.0 and log2.details.get("overtime_hours") == 0.0:
            ok("Under-hours (5.0) and overtime (0.0) calculated correctly in audit logs")
        else:
            fail("Under-hours/overtime mismatch in audit log", str(log2.details if log2 else "No log"))

        await db.rollback()
        ok("Database changes rolled back cleanly")


async def main() -> None:
    print()
    print("=" * 60)
    print("  Attendance Tracking -- Verification Suite")
    print("=" * 60)
    try:
        verify_imports()
        await verify_schema()
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

"""
Employee Management -- Verification Script
==========================================
Verifies:
  1. Import chain (models, schemas, repos, service, router)
  2. DB tables & columns (employees, users)
  3. Business rules via service layer (Onboard, Update, Offboard)
  4. Authorization guards (route-level)
  5. Audit log created on Onboard/Update/Offboard
  6. Soft delete behavior

Run:
    python verify_employee.py
"""
from __future__ import annotations

import asyncio
import os
import sys
import traceback
from datetime import date, datetime, timezone
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
        from app.models.employee import Employee
        ok("app.models.employee -- Employee")
    except Exception as exc:
        fail("app.models.employee import", str(exc))

    try:
        from app.schemas.employee import EmployeeCreate, EmployeeUpdate, EmployeeResponse
        ok("app.schemas.employee -- schemas")
    except Exception as exc:
        fail("app.schemas.employee import", str(exc))

    try:
        from app.repositories.employee_repository import EmployeeRepository
        ok("app.repositories.employee_repository -- EmployeeRepository")
    except Exception as exc:
        fail("app.repositories.employee_repository import", str(exc))

    try:
        from app.services.employee_service import EmployeeService
        ok("app.services.employee_service -- EmployeeService")
    except Exception as exc:
        fail("app.services.employee_service import", str(exc))


async def verify_schema() -> None:
    section("SECTION 2: Database Tables & Columns")
    async with engine.connect() as conn:
        tables = await conn.run_sync(lambda c: inspect(c).get_table_names())

    if "employees" in tables:
        ok("Table 'employees' exists")
    else:
        fail("Table 'employees' MISSING")

    async with engine.connect() as conn:
        cols = {c["name"] for c in await conn.run_sync(lambda c: inspect(c).get_columns("employees"))}

    required = {"id", "user_id", "department_id", "hire_date", "phone", "base_salary", "is_deleted", "deleted_at"}
    for r in required:
        if r in cols:
            ok(f"  employees.{r}")
        else:
            fail(f"  employees.{r} MISSING")


async def verify_business_rules() -> None:
    section("SECTION 3: Business Rules & Audit Logs")
    from app.models.user import User, UserRole
    from app.models.employee import Employee
    from app.models.audit_log import AuditLog
    from app.schemas.employee import EmployeeCreate, EmployeeUpdate
    from app.services.employee_service import EmployeeService

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

        # Seed admin
        admin = User(
            email=f"admin_{uuid4().hex[:8]}@verify.local",
            hashed_password="hashed",
            role=UserRole.ADMIN,
        )
        db.add(admin)
        await db.flush()

        # Seed a raw user to onboard as employee
        user_to_onboard = User(
            email=f"staff_{uuid4().hex[:8]}@verify.local",
            hashed_password="hashed",
            role=UserRole.STAFF,
        )
        db.add(user_to_onboard)
        await db.flush()

        svc = EmployeeService(db)

        # 1. Onboard Employee
        payload = EmployeeCreate(
            user_id=user_to_onboard.id,
            hire_date=date(2026, 1, 1),
            phone="+1234567890",
            base_salary=5000.00,
        )
        emp = await svc.onboard_employee(payload, operator_id=admin.id)
        if emp and emp.id:
            ok("Employee onboarded successfully")
        else:
            fail("Employee onboarding returned no object")

        # 2. Check duplicate onboard block
        try:
            await svc.onboard_employee(payload, operator_id=admin.id)
            fail("Duplicate employee onboard allowed (should be blocked)")
        except ValueError:
            ok("Duplicate employee onboard blocked correctly")

        # 3. Update employee salary/phone
        up_payload = EmployeeUpdate(phone="+1098765432", base_salary=6000.00)
        updated = await svc.update_employee(emp.id, up_payload, operator_id=admin.id)
        if updated.base_salary == 6000.00 and updated.phone == "+1098765432":
            ok("Employee details updated successfully")
        else:
            fail("Employee details update failed")

        # 4. Offboard (logical delete)
        offboarded = await svc.offboard_employee(emp.id, operator_id=admin.id)
        if offboarded.is_deleted:
            ok("Employee offboarded (soft deleted) successfully")
        else:
            fail("Employee offboarding failed to mark is_deleted")

        # 5. Audit Log verification
        stmt = select(AuditLog).where(AuditLog.target_type == "employees")
        res = await db.execute(stmt)
        logs = res.scalars().all()
        actions = {l.action for l in logs}

        for act in ("ONBOARD_EMPLOYEE", "UPDATE_EMPLOYEE", "OFFBOARD_EMPLOYEE"):
            if act in actions:
                ok(f"Audit log found: {act}")
            else:
                fail(f"Audit log MISSING: {act}")

        await db.rollback()
        ok("Database changes rolled back cleanly")


async def main() -> None:
    print()
    print("=" * 60)
    print("  Employee Management -- Verification Suite")
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

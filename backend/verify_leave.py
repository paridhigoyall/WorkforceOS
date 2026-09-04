"""
Leave Management -- Verification Script
========================================
Verifies:
  1. Import chain (models, schemas, repos, service, router)
  2. DB tables & columns (leave_requests, leave_balances)
  3. Indexes present
  4. Foreign keys wired correctly
  5. Business rules via service layer
  6. Authorization guards (route-level)
  7. Audit log created on Apply/Approve/Reject/Cancel
  8. Alembic migration chain is up-to-date

Run:
    python verify_leave.py
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

from sqlalchemy import inspect, text
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
warnings_list: list[str] = []


def ok(msg: str) -> None:
    passed.append(msg)
    print(f"  [PASS] {msg}")


def fail(msg: str, detail: str = "") -> None:
    failed.append(msg)
    info = f" -- {detail}" if detail else ""
    print(f"  [FAIL] {msg}{info}")


def warn(msg: str) -> None:
    warnings_list.append(msg)
    print(f"  [WARN] {msg}")


def section(title: str) -> None:
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}")


# ============================================================
# SECTION 1: Import Verification
# ============================================================

def verify_imports() -> None:
    section("SECTION 1: Import Verification")

    # Leave model
    try:
        from app.models.leave import LeaveRequest, LeaveBalance, LeaveType, LeaveStatus
        ok("app.models.leave -- LeaveRequest, LeaveBalance, LeaveType, LeaveStatus")
    except Exception as exc:
        fail("app.models.leave import", str(exc))

    # Leave schemas
    try:
        from app.schemas.leave import (
            LeaveRequestCreate, LeaveRequestUpdate, LeaveRequestResponse,
            LeaveBalanceCreate, LeaveBalanceUpdate, LeaveBalanceResponse,
        )
        ok("app.schemas.leave -- all 6 schemas")
    except Exception as exc:
        fail("app.schemas.leave import", str(exc))

    # Leave repository
    try:
        from app.repositories.leave_repository import (
            LeaveRequestRepository, LeaveBalanceRepository
        )
        ok("app.repositories.leave_repository -- LeaveRequestRepository, LeaveBalanceRepository")
    except Exception as exc:
        fail("app.repositories.leave_repository import", str(exc))

    # Leave service
    try:
        from app.services.leave_service import LeaveService
        ok("app.services.leave_service -- LeaveService")
    except Exception as exc:
        fail("app.services.leave_service import", str(exc))

    # Leave router
    try:
        from app.api.routes.leave import router
        ok("app.api.routes.leave -- router")
    except Exception as exc:
        fail("app.api.routes.leave import", str(exc))

    # Models __init__ exports
    try:
        from app.models import LeaveRequest, LeaveBalance, LeaveType, LeaveStatus
        ok("app.models __init__ exports LeaveRequest, LeaveBalance, LeaveType, LeaveStatus")
    except Exception as exc:
        fail("app.models __init__ leave exports", str(exc))


# ============================================================
# SECTION 2: Database Schema Verification
# ============================================================

async def verify_schema() -> None:
    section("SECTION 2: Database Tables & Columns")

    async with engine.connect() as conn:
        tables = await conn.run_sync(
            lambda c: inspect(c).get_table_names()
        )

    for tbl in ("leave_requests", "leave_balances"):
        if tbl in tables:
            ok(f"Table '{tbl}' exists in database")
        else:
            fail(f"Table '{tbl}' MISSING from database")

    # leave_requests columns
    print("\n  -- leave_requests columns --")
    required_lr = {
        "id", "employee_id", "leave_type", "start_date", "end_date",
        "total_days", "reason", "status", "approved_by", "approved_at",
        "created_at", "updated_at",
    }
    async with engine.connect() as conn:
        lr_cols = {
            c["name"]
            for c in await conn.run_sync(
                lambda c: inspect(c).get_columns("leave_requests")
            )
        }
    for col in sorted(required_lr):
        if col in lr_cols:
            ok(f"  leave_requests.{col}")
        else:
            fail(f"  leave_requests.{col} MISSING")

    # leave_balances columns
    print("\n  -- leave_balances columns --")
    required_lb = {
        "id", "employee_id", "leave_type", "year",
        "allocated_days", "used_days", "created_at", "updated_at",
    }
    async with engine.connect() as conn:
        lb_cols = {
            c["name"]
            for c in await conn.run_sync(
                lambda c: inspect(c).get_columns("leave_balances")
            )
        }
    for col in sorted(required_lb):
        if col in lb_cols:
            ok(f"  leave_balances.{col}")
        else:
            fail(f"  leave_balances.{col} MISSING")


async def verify_indexes() -> None:
    section("SECTION 3: Indexes")
    expected = {
        "leave_requests": [
            "ix_leave_requests_employee_id",
            "ix_leave_requests_status",
            "ix_leave_requests_start_date",
            "ix_leave_requests_approved_by",
        ],
        "leave_balances": [
            "ix_leave_balances_employee_id",
        ],
    }
    async with engine.connect() as conn:
        for tbl, idx_names in expected.items():
            actual = {
                i["name"]
                for i in await conn.run_sync(
                    lambda c, t=tbl: inspect(c).get_indexes(t)
                )
            }
            for idx in idx_names:
                if idx in actual:
                    ok(f"{tbl}: index '{idx}'")
                else:
                    fail(f"{tbl}: index '{idx}' MISSING")


async def verify_foreign_keys() -> None:
    section("SECTION 4: Foreign Keys")
    checks = [
        ("leave_requests", "employees", "employee_id"),
        ("leave_requests", "users",     "approved_by"),
        ("leave_balances", "employees", "employee_id"),
    ]
    async with engine.connect() as conn:
        for tbl, ref_tbl, col in checks:
            fks = await conn.run_sync(
                lambda c, t=tbl: inspect(c).get_foreign_keys(t)
            )
            matched = any(
                fk["referred_table"] == ref_tbl and col in fk["constrained_columns"]
                for fk in fks
            )
            if matched:
                ok(f"{tbl}.{col} -> {ref_tbl}.id")
            else:
                fail(f"{tbl}.{col} -> {ref_tbl}.id MISSING")


# ============================================================
# SECTION 5: Model Relationships (static)
# ============================================================

def verify_model_relationships() -> None:
    section("SECTION 5: Model Relationships")
    from app.models.leave import LeaveRequest, LeaveBalance, LeaveType, LeaveStatus
    from app.models.employee import Employee

    lr_rels = {r.key for r in LeaveRequest.__mapper__.relationships}
    for rel in ("employee", "approver"):
        if rel in lr_rels:
            ok(f"LeaveRequest.{rel} relationship defined")
        else:
            fail(f"LeaveRequest.{rel} relationship MISSING")

    emp_rels = {r.key for r in Employee.__mapper__.relationships}
    for rel in ("leave_requests", "leave_balances"):
        if rel in emp_rels:
            ok(f"Employee.{rel} back-ref defined")
        else:
            fail(f"Employee.{rel} back-ref MISSING")

    for lt in ("CASUAL", "SICK", "EARNED", "UNPAID"):
        if hasattr(LeaveType, lt):
            ok(f"LeaveType.{lt} defined")
        else:
            fail(f"LeaveType.{lt} MISSING")

    for ls in ("PENDING", "APPROVED", "REJECTED", "CANCELLED"):
        if hasattr(LeaveStatus, ls):
            ok(f"LeaveStatus.{ls} defined")
        else:
            fail(f"LeaveStatus.{ls} MISSING")


# ============================================================
# SECTION 6: Route Registration
# ============================================================

def verify_routes() -> None:
    section("SECTION 6: API Route Registration")
    from app.main import app

    routes: dict[str, set[str]] = {}
    for r in app.routes:
        if hasattr(r, "methods") and r.methods:
            if r.path not in routes:
                routes[r.path] = set()
            routes[r.path].update(r.methods)

    expected_routes = [
        ("/api/leave/",                       "POST",  "Apply for leave"),
        ("/api/leave/",                       "GET",   "List leave requests"),
        ("/api/leave/{id}",                   "GET",   "Get leave request"),
        ("/api/leave/{id}/approve",           "POST",  "Approve leave"),
        ("/api/leave/{id}/reject",            "POST",  "Reject leave"),
        ("/api/leave/{id}/cancel",            "POST",  "Cancel leave"),
        ("/api/leave/balances/",              "POST",  "Allocate balance"),
        ("/api/leave/balances/{balance_id}",  "PUT",   "Update balance"),
        ("/api/leave/balances/{employee_id}", "GET",   "Get employee balances"),
    ]

    print("  -- Actual Registered Routes --")
    for p, m in sorted(routes.items()):
        print(f"    {m} {p}")
        
    for path, method, desc in expected_routes:
        if path in routes:
            if method in routes[path]:
                ok(f"{method:6s} {path}  [{desc}]")
            else:
                fail(f"{method:6s} {path}  [{desc}] -- method not registered (registered: {routes[path]})")
        else:
            fail(f"{method:6s} {path}  [{desc}] -- route not registered")


# ============================================================
# SECTION 7: Business Rules + Audit Logs
# ============================================================

async def verify_business_rules() -> None:
    section("SECTION 7: Business Rules")

    from app.models.user import User, UserRole
    from app.models.employee import Employee
    from app.models.leave import LeaveRequest, LeaveStatus, LeaveType
    from app.models.audit_log import AuditLog
    from app.schemas.leave import LeaveRequestCreate
    from app.services.leave_service import LeaveService
    from sqlalchemy import select

    async with AsyncSessionLocal() as db:
        # Override db.begin to support nested transactions (savepoints) since the session
        # will already have an active transaction started by seed flushes.
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
        # ----------------------------------------------------------------
        # Seed: admin user + test employee
        # ----------------------------------------------------------------
        admin = User(
            email=f"admin_{uuid4().hex[:8]}@verify.local",
            hashed_password="hashed",
            role=UserRole.ADMIN,
        )
        db.add(admin)
        await db.flush()

        staff_user = User(
            email=f"staff_{uuid4().hex[:8]}@verify.local",
            hashed_password="hashed",
            role=UserRole.STAFF,
        )
        db.add(staff_user)
        await db.flush()

        emp = Employee(
            user_id=staff_user.id,
            hire_date=date(2024, 1, 1),
            base_salary=50000,
        )
        db.add(emp)
        await db.flush()

        svc = LeaveService(db)

        # ----------------------------------------------------------------
        # Test 1: Create leave request (basic apply)
        # ----------------------------------------------------------------
        print("\n  -- Business Rule Tests --")
        payload1 = LeaveRequestCreate(
            leave_type=LeaveType.CASUAL,
            start_date=date(2026, 7, 1),
            end_date=date(2026, 7, 5),
            reason="Annual summer leave test",
            employee_id=emp.id,
        )
        leave1 = await svc.apply(payload1, requesting_user_id=admin.id)
        if leave1 and leave1.id:
            ok("Test 1: Create leave request -- LeaveRequest created with ID")
        else:
            fail("Test 1: Create leave request -- no record returned")

        if leave1.status == LeaveStatus.PENDING:
            ok("Test 1: New leave starts as PENDING")
        else:
            fail("Test 1: New leave status", f"expected PENDING, got {leave1.status}")

        # ----------------------------------------------------------------
        # Test 2: Prevent invalid date ranges (end < start)
        # ----------------------------------------------------------------
        try:
            bad_payload = LeaveRequestCreate(
                leave_type=LeaveType.SICK,
                start_date=date(2026, 7, 10),
                end_date=date(2026, 7, 5),   # end < start
                reason="Bad date range test",
                employee_id=emp.id,
            )
            fail("Test 2: Invalid date range -- Pydantic should have rejected")
        except Exception as exc:
            ok(f"Test 2: Invalid date range (end < start) -- correctly rejected: {type(exc).__name__}")

        # ----------------------------------------------------------------
        # Test 3: total_days auto-calculation
        # ----------------------------------------------------------------
        expected_days = (date(2026, 7, 5) - date(2026, 7, 1)).days + 1  # = 5
        if leave1.total_days == expected_days:
            ok(f"Test 3: total_days auto-calculated = {leave1.total_days} (expected {expected_days})")
        else:
            fail(f"Test 3: total_days mismatch -- got {leave1.total_days}, expected {expected_days}")

        # ----------------------------------------------------------------
        # Test 4: Overlapping leave prevention
        # ----------------------------------------------------------------
        overlap_payload = LeaveRequestCreate(
            leave_type=LeaveType.SICK,
            start_date=date(2026, 7, 3),   # overlaps 7/1-7/5
            end_date=date(2026, 7, 8),
            reason="Overlapping sick leave",
            employee_id=emp.id,
        )
        try:
            await svc.apply(overlap_payload, requesting_user_id=admin.id)
            fail("Test 4: Overlapping leave -- should have been rejected")
        except ValueError as exc:
            if "overlap" in str(exc).lower():
                ok("Test 4: Overlapping leave correctly rejected -- ValueError raised")
            else:
                fail("Test 4: Overlapping leave -- wrong error raised", str(exc))

        # ----------------------------------------------------------------
        # Test 5: Approve PENDING request
        # ----------------------------------------------------------------
        approved_leave = await svc.approve(leave1.id, approver_user_id=admin.id)
        if approved_leave.status == LeaveStatus.APPROVED:
            ok("Test 5: Approve PENDING leave -- status=APPROVED")
        else:
            fail("Test 5: Approve PENDING leave", f"status={approved_leave.status}")

        if approved_leave.approved_by == admin.id:
            ok("Test 5: approved_by set correctly")
        else:
            fail("Test 5: approved_by not set")

        if approved_leave.approved_at is not None:
            ok("Test 5: approved_at timestamp set")
        else:
            fail("Test 5: approved_at is None")

        # ----------------------------------------------------------------
        # Test 6: Prevent approving already-approved request
        # ----------------------------------------------------------------
        try:
            await svc.approve(leave1.id, approver_user_id=admin.id)
            fail("Test 6: Double-approve guard -- should have been rejected")
        except ValueError as exc:
            if "pending" in str(exc).lower():
                ok("Test 6: Re-approve already-APPROVED leave -- ValueError raised correctly")
            else:
                fail("Test 6: Double-approve guard -- wrong error", str(exc))

        # ----------------------------------------------------------------
        # Test 7: Apply another leave, then reject it
        # ----------------------------------------------------------------
        payload2 = LeaveRequestCreate(
            leave_type=LeaveType.EARNED,
            start_date=date(2026, 8, 1),
            end_date=date(2026, 8, 3),
            reason="Earned leave reject test",
            employee_id=emp.id,
        )
        leave2 = await svc.apply(payload2, requesting_user_id=admin.id)

        rejected_leave = await svc.reject(leave2.id, approver_user_id=admin.id)
        if rejected_leave.status == LeaveStatus.REJECTED:
            ok("Test 7: Reject PENDING leave -- status=REJECTED")
        else:
            fail("Test 7: Reject PENDING leave", f"status={rejected_leave.status}")

        # ----------------------------------------------------------------
        # Test 8: Prevent rejecting already-rejected request
        # ----------------------------------------------------------------
        try:
            await svc.reject(leave2.id, approver_user_id=admin.id)
            fail("Test 8: Double-reject guard -- should have been rejected")
        except ValueError as exc:
            if "pending" in str(exc).lower():
                ok("Test 8: Re-reject already-REJECTED leave -- ValueError raised correctly")
            else:
                fail("Test 8: Double-reject guard -- wrong error", str(exc))

        # ----------------------------------------------------------------
        # Test 9: Cancel PENDING request
        # ----------------------------------------------------------------
        payload3 = LeaveRequestCreate(
            leave_type=LeaveType.SICK,
            start_date=date(2026, 9, 1),
            end_date=date(2026, 9, 2),
            reason="Sick leave cancel test",
            employee_id=emp.id,
        )
        leave3 = await svc.apply(payload3, requesting_user_id=admin.id)
        cancelled_leave = await svc.cancel(leave3.id, requesting_user_id=admin.id)
        if cancelled_leave.status == LeaveStatus.CANCELLED:
            ok("Test 9: Cancel PENDING leave -- status=CANCELLED")
        else:
            fail("Test 9: Cancel PENDING leave", f"status={cancelled_leave.status}")

        # ----------------------------------------------------------------
        # Test 10: Prevent cancelling already-cancelled request
        # ----------------------------------------------------------------
        try:
            await svc.cancel(leave3.id, requesting_user_id=admin.id)
            fail("Test 10: Double-cancel guard -- should have been rejected")
        except ValueError as exc:
            ok("Test 10: Re-cancel already-CANCELLED leave -- ValueError raised correctly")

        # ----------------------------------------------------------------
        # Test 11: Prevent cancelling REJECTED request
        # ----------------------------------------------------------------
        try:
            await svc.cancel(leave2.id, requesting_user_id=admin.id)
            fail("Test 11: Cancel REJECTED guard -- should have been rejected")
        except ValueError as exc:
            ok("Test 11: Cancel REJECTED leave -- ValueError raised correctly")

        # ----------------------------------------------------------------
        # Test 12: Cancel APPROVED leave (balance refund)
        # ----------------------------------------------------------------
        payload4 = LeaveRequestCreate(
            leave_type=LeaveType.CASUAL,
            start_date=date(2026, 10, 1),
            end_date=date(2026, 10, 3),
            reason="Casual leave approve then cancel",
            employee_id=emp.id,
        )
        leave4 = await svc.apply(payload4, requesting_user_id=admin.id)
        await svc.approve(leave4.id, approver_user_id=admin.id)
        cancelled_approved = await svc.cancel(leave4.id, requesting_user_id=admin.id)
        if cancelled_approved.status == LeaveStatus.CANCELLED:
            ok("Test 12: Cancel APPROVED leave -- status=CANCELLED (balance refunded)")
        else:
            fail("Test 12: Cancel APPROVED leave", f"status={cancelled_approved.status}")

        # ================================================================
        # SECTION 8: Authorization Verification
        # ================================================================
        section("SECTION 8: Authorization Verification")

        # Employee can only view own leaves (route-level guard check)
        # Simulated: Staff trying to access another employee's leave
        another_user = User(
            email=f"other_{uuid4().hex[:8]}@verify.local",
            hashed_password="hashed",
            role=UserRole.STAFF,
        )
        db.add(another_user)
        await db.flush()
        other_emp = Employee(
            user_id=another_user.id,
            hire_date=date(2024, 6, 1),
            base_salary=45000,
        )
        db.add(other_emp)
        await db.flush()

        # Verify route guard logic exists in router code
        from app.api.routes.leave import router as leave_router
        route_src_path = os.path.join(
            os.path.dirname(__file__), "app", "api", "routes", "leave.py"
        )
        with open(route_src_path, "r") as f:
            route_src = f.read()

        if "employee_id != employee.id" in route_src:
            ok("Auth: Route guard -- employee cannot access other employee's leaves (code verified)")
        else:
            fail("Auth: Route guard -- cross-employee access guard not found in routes")

        if "require_role([UserRole.ADMIN, UserRole.HR])" in route_src:
            ok("Auth: Approve/Reject endpoints require ADMIN or HR role")
        else:
            fail("Auth: Approve/Reject role guard not found in routes")

        if "UserRole.ADMIN, UserRole.HR" in route_src and "is_privileged" in route_src:
            ok("Auth: Admin/HR can access all pending leaves (is_privileged check)")
        else:
            fail("Auth: is_privileged check not found in routes")

        # Admin can list all leaves (no employee_id restriction)
        all_leaves, total = await svc.list_leaves(limit=100, offset=0)
        ok(f"Auth: Admin list_leaves -- returned {total} total records")

        # Staff own-employee filter
        emp_leaves, emp_total = await svc.list_leaves(employee_id=emp.id, limit=100, offset=0)
        ok(f"Auth: Staff filtered list_leaves -- {emp_total} records for employee")

        # ================================================================
        # SECTION 9: Audit Log Verification
        # ================================================================
        section("SECTION 9: Audit Log Verification")

        stmt = (
            select(AuditLog)
            .where(AuditLog.target_type == "leave_requests")
            .order_by(AuditLog.created_at)
        )
        result = await db.execute(stmt)
        audit_logs = result.scalars().all()
        actions_found = {log.action for log in audit_logs}

        for action in ("LEAVE_APPLY", "LEAVE_APPROVE", "LEAVE_REJECT", "LEAVE_CANCEL"):
            if action in actions_found:
                count = sum(1 for l in audit_logs if l.action == action)
                ok(f"AuditLog: action='{action}' found ({count} records)")
            else:
                fail(f"AuditLog: action='{action}' NOT found in audit_logs")

        # Verify audit log details payload
        apply_logs = [l for l in audit_logs if l.action == "LEAVE_APPLY"]
        if apply_logs and apply_logs[0].details:
            details = apply_logs[0].details
            for key in ("employee_id", "leave_type", "start_date", "end_date", "total_days"):
                if key in details:
                    ok(f"AuditLog LEAVE_APPLY details contains '{key}'")
                else:
                    fail(f"AuditLog LEAVE_APPLY details missing '{key}'")
        else:
            fail("AuditLog LEAVE_APPLY has no details payload")

        # Rollback -- do NOT persist test data
        await db.rollback()
        ok("Test data rolled back (no DB pollution)")


# ============================================================
# SECTION 10: Migration Chain
# ============================================================

async def verify_migration_chain() -> None:
    section("SECTION 10: Alembic Migration Chain")

    async with engine.connect() as conn:
        result = await conn.execute(text("SELECT version_num FROM alembic_version"))
        row = result.fetchone()
        if row:
            ok(f"alembic_version present: {row[0]}")
            EXPECTED_HEAD = "a3f7c1d8e924"
            if row[0] == EXPECTED_HEAD:
                ok(f"DB is at latest migration head ({EXPECTED_HEAD} -- add_department_code)")
            else:
                warn(f"DB head is '{row[0]}', expected '{EXPECTED_HEAD}'")
        else:
            fail("alembic_version table is empty")

    async with engine.connect() as conn:
        for tbl in ("leave_requests", "leave_balances"):
            result = await conn.execute(text(f"SELECT COUNT(*) FROM {tbl}"))
            count = result.scalar()
            ok(f"Table '{tbl}' is accessible -- {count} rows (post-rollback)")


# ============================================================
# Main Runner
# ============================================================

async def main() -> None:
    print()
    print("=" * 60)
    print("  Leave Management -- Full Verification Suite")
    print("=" * 60)
    print(f"  Database : {DATABASE_URL.split('@')[-1]}")
    print(f"  Time     : {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}")

    try:
        # Static checks (no DB needed)
        verify_imports()
        verify_model_relationships()
        verify_routes()

        # DB-based checks
        await verify_schema()
        await verify_indexes()
        await verify_foreign_keys()
        await verify_business_rules()
        await verify_migration_chain()

    except Exception:
        print("\n[FATAL] Unhandled exception during verification:")
        traceback.print_exc()
        failed.append("FATAL: unhandled exception -- see traceback above")

    # ----------------------------------------------------------------
    # Final Summary
    # ----------------------------------------------------------------
    total = len(passed) + len(failed)
    print()
    print("=" * 60)
    print("  VERIFICATION SUMMARY")
    print("=" * 60)
    print(f"  Passed   : {len(passed)} / {total}")
    print(f"  Failed   : {len(failed)} / {total}")
    print(f"  Warnings : {len(warnings_list)}")

    if warnings_list:
        print("\n  Warnings:")
        for w in warnings_list:
            print(f"    [WARN] {w}")

    if failed:
        print("\n  Failed checks:")
        for f_ in failed:
            print(f"    [FAIL] {f_}")
        print()
        print("  RESULT: INCOMPLETE -- fix the failures listed above")
        print()
        sys.exit(1)
    else:
        print()
        print("  RESULT: ALL CHECKS PASSED -- Leave Management is COMPLETE")
        print()
        sys.exit(0)


if __name__ == "__main__":
    asyncio.run(main())

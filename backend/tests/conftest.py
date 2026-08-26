from __future__ import annotations

import os
import sys
from typing import AsyncGenerator
from uuid import uuid4
from datetime import date, datetime, timezone
import pytest
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.pool import NullPool

# Ensure backend root is on sys.path
BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

from app.main import app
from app.core.database import get_db
from app.core.security import get_password_hash, create_access_token
from app.models.base import Base
from app.models.user import User, UserRole
from app.models.department import Department
from app.models.employee import Employee
from app.models.attendance import Attendance, AttendanceStatus
from app.models.leave import LeaveRequest, LeaveType, LeaveStatus, LeaveBalance
from app.models.payroll import PayrollPeriod, PayrollPeriodStatus, PayrollRecord, PayrollRecordStatus
from app.models.notification import Notification, NotificationType

TEST_DATABASE_URL = os.getenv(
    "TEST_DATABASE_URL",
    os.getenv("DATABASE_URL", "postgresql+asyncpg://postgres:postgres@localhost:5432/postgres"),
)

test_engine = create_async_engine(
    TEST_DATABASE_URL,
    poolclass=NullPool,
    echo=False,
)

TestingSessionLocal = async_sessionmaker(
    bind=test_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    # Do NOT autobegin here; let services manage their own transactions
)


@pytest.fixture(scope="session", autouse=True)
async def create_db_schema():
    """Create all tables once per test session."""
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    # Optionally drop tables after all tests; commented out for speed:
    # async with test_engine.begin() as conn:
    #     await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Provide an isolated AsyncSession per test.

    Each test gets a brand-new session that is NOT inside a pre-begun
    transaction, so services that call `session.begin()` work correctly.
    After the test, we rollback any uncommitted state and close the session.
    """
    async with TestingSessionLocal() as session:
        yield session
        # Roll back any uncommitted changes so tests are isolated
        await session.rollback()


@pytest.fixture
async def client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """FastAPI Async HTTP Client with db_session dependency override."""
    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as ac:
        yield ac
    app.dependency_overrides.clear()


# ============================================================================
# USER & ROLE FIXTURES
# ============================================================================

@pytest.fixture
async def admin_user(db_session: AsyncSession) -> User:
    user = User(
        id=uuid4(),
        email=f"admin_{uuid4().hex[:8]}@example.com",
        hashed_password=get_password_hash("AdminPass123!"),
        role=UserRole.ADMIN,
        is_mfa_enabled=False,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest.fixture
def admin_token(admin_user: User) -> str:
    return create_access_token({"sub": str(admin_user.id), "role": admin_user.role.value})


@pytest.fixture
def admin_headers(admin_token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {admin_token}"}


@pytest.fixture
async def hr_user(db_session: AsyncSession) -> User:
    user = User(
        id=uuid4(),
        email=f"hr_{uuid4().hex[:8]}@example.com",
        hashed_password=get_password_hash("HRPass123!"),
        role=UserRole.HR,
        is_mfa_enabled=False,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest.fixture
def hr_token(hr_user: User) -> str:
    return create_access_token({"sub": str(hr_user.id), "role": hr_user.role.value})


@pytest.fixture
def hr_headers(hr_token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {hr_token}"}


@pytest.fixture
async def staff_user(db_session: AsyncSession) -> User:
    user = User(
        id=uuid4(),
        email=f"staff_{uuid4().hex[:8]}@example.com",
        hashed_password=get_password_hash("StaffPass123!"),
        role=UserRole.STAFF,
        is_mfa_enabled=False,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest.fixture
def staff_token(staff_user: User) -> str:
    return create_access_token({"sub": str(staff_user.id), "role": staff_user.role.value})


@pytest.fixture
def staff_headers(staff_token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {staff_token}"}


# ============================================================================
# DOMAIN ENTITY FIXTURES
# ============================================================================

@pytest.fixture
async def test_department(db_session: AsyncSession) -> Department:
    dept = Department(
        id=uuid4(),
        name=f"Engineering_{uuid4().hex[:6]}",
        description="Core Product Engineering",
    )
    db_session.add(dept)
    await db_session.commit()
    await db_session.refresh(dept)
    return dept


@pytest.fixture
async def test_employee(
    db_session: AsyncSession,
    staff_user: User,
    test_department: Department,
) -> Employee:
    emp = Employee(
        id=uuid4(),
        user_id=staff_user.id,
        department_id=test_department.id,
        hire_date=date(2025, 1, 1),
        base_salary=6000.00,
        phone="+15551234567",
        is_deleted=False,
    )
    db_session.add(emp)
    await db_session.commit()
    await db_session.refresh(emp)
    return emp

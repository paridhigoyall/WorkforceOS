from __future__ import annotations

import pytest
from uuid import uuid4
from httpx import AsyncClient

from app.models.user import User, UserRole
from app.models.department import Department
from app.models.employee import Employee
from app.core.security import get_password_hash
from sqlalchemy.ext.asyncio import AsyncSession


class TestEmployeeAPI:
    async def test_onboard_employee_admin(
        self,
        client: AsyncClient,
        admin_headers: dict[str, str],
        test_department: Department,
        db_session: AsyncSession,
    ):
        # Create user account for onboarding
        user = User(
            id=uuid4(),
            email=f"emp_api_{uuid4().hex[:6]}@test.com",
            hashed_password=get_password_hash("StrongPass123!"),
            role=UserRole.STAFF,
        )
        db_session.add(user)
        await db_session.flush()

        res = await client.post(
            "/api/employees/onboard",
            headers=admin_headers,
            json={
                "user_id": str(user.id),
                "department_id": str(test_department.id),
                "hire_date": "2025-01-15",
                "base_salary": 5000.0,
                "phone": "+1234567890",
            },
        )
        assert res.status_code == 201
        data = res.json()
        assert data["user_id"] == str(user.id)
        assert data["department_id"] == str(test_department.id)

    async def test_onboard_employee_staff_forbidden(
        self,
        client: AsyncClient,
        staff_headers: dict[str, str],
        test_department: Department,
    ):
        res = await client.post(
            "/api/employees/onboard",
            headers=staff_headers,
            json={
                "user_id": str(uuid4()),
                "department_id": str(test_department.id),
                "hire_date": "2025-01-15",
                "base_salary": 4000.0,
            },
        )
        assert res.status_code == 403

    async def test_list_employees(
        self,
        client: AsyncClient,
        admin_headers: dict[str, str],
        test_employee: Employee,
    ):
        res = await client.get("/api/employees/", headers=admin_headers)
        assert res.status_code == 200
        data = res.json()
        assert isinstance(data, list)
        assert len(data) >= 1

    async def test_update_employee(
        self,
        client: AsyncClient,
        admin_headers: dict[str, str],
        test_employee: Employee,
    ):
        res = await client.put(
            f"/api/employees/{test_employee.id}",
            headers=admin_headers,
            json={"base_salary": 8000.0, "phone": "+1122334455"},
        )
        assert res.status_code == 200
        assert res.json()["base_salary"] == 8000.0

    async def test_delete_employee(
        self,
        client: AsyncClient,
        admin_headers: dict[str, str],
        test_employee: Employee,
    ):
        res = await client.delete(
            f"/api/employees/{test_employee.id}",
            headers=admin_headers,
        )
        assert res.status_code == 200
        assert res.json()["is_deleted"] is True

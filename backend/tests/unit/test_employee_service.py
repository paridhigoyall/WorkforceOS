from __future__ import annotations

import pytest
from datetime import date
from uuid import uuid4
from decimal import Decimal
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User, UserRole
from app.models.department import Department
from app.models.employee import Employee
from app.schemas.employee import EmployeeCreate, EmployeeUpdate
from app.services.employee_service import EmployeeService


class TestEmployeeService:
    async def test_onboard_employee_success(
        self,
        db_session: AsyncSession,
        admin_user: User,
        staff_user: User,
        test_department: Department,
    ):
        service = EmployeeService(db_session)
        schema = EmployeeCreate(
            user_id=staff_user.id,
            department_id=test_department.id,
            hire_date=date(2025, 2, 1),
            base_salary=Decimal("5500.00"),
            phone="+1234567890",
        )
        emp = await service.onboard_employee(schema, operator_id=admin_user.id)

        assert emp.id is not None
        assert emp.user_id == staff_user.id
        assert emp.department_id == test_department.id
        assert float(emp.base_salary) == 5500.00
        assert emp.is_deleted is False

    async def test_onboard_duplicate_user_fails(
        self,
        db_session: AsyncSession,
        admin_user: User,
        test_employee: Employee,
        test_department: Department,
    ):
        service = EmployeeService(db_session)
        schema = EmployeeCreate(
            user_id=test_employee.user_id,
            department_id=test_department.id,
            hire_date=date(2025, 2, 1),
            base_salary=Decimal("5000.00"),
        )
        with pytest.raises(ValueError, match="already onboarded"):
            await service.onboard_employee(schema, operator_id=admin_user.id)

    async def test_update_employee_success(
        self,
        db_session: AsyncSession,
        admin_user: User,
        test_employee: Employee,
    ):
        service = EmployeeService(db_session)
        update_data = EmployeeUpdate(
            base_salary=Decimal("7500.00"),
            phone="+19876543210",
        )
        updated = await service.update_employee(test_employee.id, update_data, operator_id=admin_user.id)

        assert float(updated.base_salary) == 7500.00
        assert updated.phone == "+19876543210"

    async def test_update_nonexistent_employee_fails(
        self,
        db_session: AsyncSession,
        admin_user: User,
    ):
        service = EmployeeService(db_session)
        with pytest.raises(ValueError, match="not found"):
            await service.update_employee(uuid4(), EmployeeUpdate(base_salary=Decimal("1000.00")), operator_id=admin_user.id)

    async def test_offboard_employee_soft_delete(
        self,
        db_session: AsyncSession,
        admin_user: User,
        test_employee: Employee,
    ):
        service = EmployeeService(db_session)
        offboarded = await service.offboard_employee(test_employee.id, operator_id=admin_user.id)

        assert offboarded.is_deleted is True
        assert offboarded.deleted_at is not None

        # Verifying the employee is no longer returned by get_employee
        with pytest.raises(ValueError, match="not found"):
            await service.get_employee(test_employee.id)


from __future__ import annotations

import pytest
from uuid import uuid4
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.department import Department
from app.schemas.department import DepartmentCreate, DepartmentUpdate
from app.services.department_service import DepartmentService


class TestDepartmentService:
    async def test_create_department_success(
        self,
        db_session: AsyncSession,
    ):
        service = DepartmentService(db_session)
        name = f"Analytics_{uuid4().hex[:6]}"
        schema = DepartmentCreate(
            name=name,
            description="Business Analytics",
        )
        dept = await service.create_department(schema)

        assert dept.id is not None
        assert dept.name == name
        assert dept.is_deleted is False

    async def test_create_duplicate_name_fails(
        self,
        db_session: AsyncSession,
        test_department: Department,
    ):
        service = DepartmentService(db_session)
        schema = DepartmentCreate(
            name=test_department.name,
            description="Duplicate Name Dept",
        )
        with pytest.raises(ValueError, match="already exists"):
            await service.create_department(schema)

    async def test_update_department(
        self,
        db_session: AsyncSession,
        test_department: Department,
    ):
        service = DepartmentService(db_session)
        updated = await service.update_department(
            test_department.id,
            DepartmentUpdate(description="Updated Description"),
        )
        assert updated.description == "Updated Description"

    async def test_delete_department_soft_delete(
        self,
        db_session: AsyncSession,
        test_department: Department,
    ):
        service = DepartmentService(db_session)
        deleted = await service.delete_department(test_department.id)
        assert deleted.is_deleted is True
        assert deleted.deleted_at is not None

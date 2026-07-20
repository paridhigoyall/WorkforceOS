from typing import List, Optional, Tuple
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.department import Department
from app.repositories.department_repository import DepartmentRepository
from app.schemas.department import DepartmentCreate, DepartmentUpdate


class DepartmentService:
    def __init__(self, db_session: AsyncSession) -> None:
        self.db_session = db_session
        self.repo = DepartmentRepository(db_session)

    async def create_department(self, schema: DepartmentCreate) -> Department:
        """
        Business workflow to create a department.
        Validates uniqueness of name and handles database transactions.
        """
        async with self.db_session.begin():
            # Check if name is already taken
            existing = await self.repo.get_by_name(schema.name, include_deleted=True)
            if existing:
                if existing.is_deleted:
                    raise ValueError(
                        f"Department '{schema.name}' already exists but was soft-deleted. "
                        "Please restore it instead of creating a new one."
                    )
                raise ValueError(f"Department with name '{schema.name}' already exists.")

            db_dept = await self.repo.create(schema)
            
        return db_dept

    async def get_department(self, id: UUID) -> Department:
        """Retrieve department by ID, raising error if not found."""
        db_dept = await self.repo.get_by_id(id)
        if not db_dept:
            raise ValueError(f"Department with ID {id} not found.")
        return db_dept

    async def list_departments(
        self, 
        limit: int = 100, 
        offset: int = 0
    ) -> Tuple[List[Department], int]:
        """List active departments with total count."""
        return await self.repo.list_paginated(limit=limit, offset=offset)

    async def update_department(self, id: UUID, schema: DepartmentUpdate) -> Department:
        """
        Business workflow to update department details.
        Ensures name changes do not cause unique constraint violations.
        """
        db_dept = await self.get_department(id)

        async with self.db_session.begin():
            if schema.name and schema.name != db_dept.name:
                existing = await self.repo.get_by_name(schema.name, include_deleted=True)
                if existing:
                    raise ValueError(f"Cannot update department name to '{schema.name}' as it already exists.")
            
            db_dept = await self.repo.update(db_dept, schema)
            
        return db_dept

    async def delete_department(self, id: UUID) -> Department:
        """
        Soft deletes the department and commits transaction.
        """
        db_dept = await self.get_department(id)
        async with self.db_session.begin():
            db_dept = await self.repo.delete(db_dept)
            
        return db_dept


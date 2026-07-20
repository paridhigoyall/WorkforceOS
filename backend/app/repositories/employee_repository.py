from datetime import datetime, timezone
from typing import List, Optional, Tuple
from uuid import UUID
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.models.employee import Employee
from app.schemas.employee import EmployeeCreate, EmployeeUpdate


class EmployeeRepository:
    def __init__(self, db_session: AsyncSession) -> None:
        self.db_session = db_session

    async def create(self, schema: EmployeeCreate) -> Employee:
        """Create a new employee record."""
        db_emp = Employee(
            user_id=schema.user_id,
            department_id=schema.department_id,
            hire_date=schema.hire_date,
            phone=schema.phone,
            base_salary=schema.base_salary
        )
        self.db_session.add(db_emp)
        await self.db_session.flush()
        
        # Reload to populate relationships (e.g. department, user) if needed
        return await self.get_by_id(db_emp.id)  # type: ignore

    async def get_by_id(self, id: UUID, include_deleted: bool = False) -> Optional[Employee]:
        """
        Fetch an employee by their unique UUID.
        Prefetches the associated user and department relations using joinedload.
        """
        stmt = (
            select(Employee)
            .options(joinedload(Employee.user), joinedload(Employee.department))
            .where(Employee.id == id)
        )
        if not include_deleted:
            stmt = stmt.where(Employee.is_deleted == False)
            
        result = await self.db_session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_user_id(self, user_id: UUID, include_deleted: bool = False) -> Optional[Employee]:
        """
        Fetch an employee by their associated User ID.
        Prefetches the associated user and department relations.
        """
        stmt = (
            select(Employee)
            .options(joinedload(Employee.user), joinedload(Employee.department))
            .where(Employee.user_id == user_id)
        )
        if not include_deleted:
            stmt = stmt.where(Employee.is_deleted == False)
            
        result = await self.db_session.execute(stmt)
        return result.scalar_one_or_none()

    async def update(self, db_obj: Employee, schema: EmployeeUpdate) -> Employee:
        """Update an existing employee record."""
        update_data = schema.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(db_obj, key, value)
            
        self.db_session.add(db_obj)
        await self.db_session.flush()
        return await self.get_by_id(db_obj.id)  # type: ignore

    async def delete(self, db_obj: Employee) -> Employee:
        """Soft delete an employee record."""
        db_obj.is_deleted = True
        db_obj.deleted_at = datetime.now(timezone.utc)
        self.db_session.add(db_obj)
        await self.db_session.flush()
        return db_obj

    async def list_paginated(
        self,
        department_id: Optional[UUID] = None,
        limit: int = 100,
        offset: int = 0,
        include_deleted: bool = False
    ) -> Tuple[List[Employee], int]:
        """
        Fetch a paginated, filtered list of employees and return (records, total_count).
        Allows optional filtering by department_id.
        """
        # Base queries
        query_stmt = select(Employee).options(
            joinedload(Employee.user), 
            joinedload(Employee.department)
        )
        count_stmt = select(func.count()).select_from(Employee)

        # Filters
        if not include_deleted:
            query_stmt = query_stmt.where(Employee.is_deleted == False)
            count_stmt = count_stmt.where(Employee.is_deleted == False)
            
        if department_id:
            query_stmt = query_stmt.where(Employee.department_id == department_id)
            count_stmt = count_stmt.where(Employee.department_id == department_id)

        # Execute total count
        count_result = await self.db_session.execute(count_stmt)
        total_count = count_result.scalar_one() or 0

        # Execute paginated query (ordered by created_at)
        query_stmt = query_stmt.order_by(Employee.created_at.desc()).offset(offset).limit(limit)
        query_result = await self.db_session.execute(query_stmt)
        records = list(query_result.scalars().all())

        return records, total_count

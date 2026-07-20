from datetime import datetime, timezone
from typing import List, Optional, Tuple
from uuid import UUID
from sqlalchemy import select, func, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.department import Department
from app.schemas.department import DepartmentCreate, DepartmentUpdate


class DepartmentRepository:
    def __init__(self, db_session: AsyncSession) -> None:
        self.db_session = db_session

    async def create(self, schema: DepartmentCreate) -> Department:
        """Create a new department."""
        db_dept = Department(
            name=schema.name,
            description=schema.description
        )
        self.db_session.add(db_dept)
        await self.db_session.flush()  # Populates ID and DB defaults
        return db_dept

    async def get_by_id(self, id: UUID, include_deleted: bool = False) -> Optional[Department]:
        """Fetch a department by its unique UUID."""
        stmt = select(Department).where(Department.id == id)
        if not include_deleted:
            stmt = stmt.where(Department.is_deleted == False)
        
        result = await self.db_session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_name(self, name: str, include_deleted: bool = False) -> Optional[Department]:
        """Fetch a department by its unique name."""
        stmt = select(Department).where(Department.name == name)
        if not include_deleted:
            stmt = stmt.where(Department.is_deleted == False)
            
        result = await self.db_session.execute(stmt)
        return result.scalar_one_or_none()

    async def update(self, db_obj: Department, schema: DepartmentUpdate) -> Department:
        """Update an existing department object."""
        update_data = schema.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(db_obj, key, value)
            
        self.db_session.add(db_obj)
        await self.db_session.flush()
        return db_obj

    async def delete(self, db_obj: Department) -> Department:
        """Perform a soft delete on a department."""
        db_obj.is_deleted = True
        db_obj.deleted_at = datetime.now(timezone.utc)
        self.db_session.add(db_obj)
        await self.db_session.flush()
        return db_obj

    async def list_paginated(
        self, 
        limit: int = 100, 
        offset: int = 0, 
        include_deleted: bool = False
    ) -> Tuple[List[Department], int]:
        """
        Fetch a paginated list of departments and return (records, total_count).
        Excludes soft-deleted departments by default.
        """
        # Base queries
        query_stmt = select(Department)
        count_stmt = select(func.count()).select_from(Department)

        if not include_deleted:
            query_stmt = query_stmt.where(Department.is_deleted == False)
            count_stmt = count_stmt.where(Department.is_deleted == False)

        # Execute total count
        count_result = await self.db_session.execute(count_stmt)
        total_count = count_result.scalar_one() or 0

        # Execute paginated fetch (ordered by created_at)
        query_stmt = query_stmt.order_by(Department.created_at.desc()).offset(offset).limit(limit)
        query_result = await self.db_session.execute(query_stmt)
        records = list(query_result.scalars().all())

        return records, total_count

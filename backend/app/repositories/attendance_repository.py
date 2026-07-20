"""
Attendance repository layer.

Follows the workforce management repository conventions:
  - Takes an AsyncSession via __init__
  - Interacts with DB using SQLAlchemy 2.0 select queries
  - Performs flushes instead of commits (transaction boundary managed by service layer)
  - Uses joinedload/selectinload to eager-load relationships where appropriate
"""
from __future__ import annotations

from datetime import date
from typing import List, Optional, Tuple
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.models.attendance import Attendance
from app.schemas.attendance import AttendanceCreate, AttendanceUpdate


class AttendanceRepository:
    """Handles CRUD database operations for Attendance records."""

    def __init__(self, db_session: AsyncSession) -> None:
        self.db_session = db_session

    async def create(self, schema: AttendanceCreate) -> Attendance:
        """Create a new attendance record."""
        db_attendance = Attendance(
            employee_id=schema.employee_id,
            attendance_date=schema.attendance_date,
            check_in_time=schema.check_in_time,
            attendance_status=schema.attendance_status,
        )
        self.db_session.add(db_attendance)
        await self.db_session.flush()
        
        # Load related data (e.g. employee) and return the saved object
        return await self.get_by_id(db_attendance.id)  # type: ignore

    async def get_by_id(self, id: UUID) -> Optional[Attendance]:
        """Fetch a single attendance record by ID."""
        stmt = (
            select(Attendance)
            .options(joinedload(Attendance.employee))
            .where(Attendance.id == id)
        )
        result = await self.db_session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_employee_and_date(self, employee_id: UUID, attendance_date: date) -> Optional[Attendance]:
        """Fetch an attendance record for a specific employee on a specific date."""
        stmt = (
            select(Attendance)
            .options(joinedload(Attendance.employee))
            .where(
                Attendance.employee_id == employee_id,
                Attendance.attendance_date == attendance_date,
            )
        )
        result = await self.db_session.execute(stmt)
        return result.scalar_one_or_none()

    async def update(self, db_obj: Attendance, schema: AttendanceUpdate) -> Attendance:
        """Update fields on an existing attendance record."""
        update_data = schema.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(db_obj, key, value)
            
        self.db_session.add(db_obj)
        await self.db_session.flush()
        return await self.get_by_id(db_obj.id)  # type: ignore

    async def list_paginated(
        self,
        employee_id: Optional[UUID] = None,
        limit: int = 100,
        offset: int = 0
    ) -> Tuple[List[Attendance], int]:
        """Fetch paginated, optionally filtered list of attendance records, returning (records, count)."""
        query_stmt = select(Attendance).options(joinedload(Attendance.employee))
        count_stmt = select(func.count()).select_from(Attendance)

        if employee_id:
            query_stmt = query_stmt.where(Attendance.employee_id == employee_id)
            count_stmt = count_stmt.where(Attendance.employee_id == employee_id)

        # Count total records matching criteria
        count_result = await self.db_session.execute(count_stmt)
        total_count = count_result.scalar_one() or 0

        # Run paginated, sorted query
        query_stmt = (
            query_stmt.order_by(
                Attendance.attendance_date.desc(),
                Attendance.check_in_time.desc()
            )
            .offset(offset)
            .limit(limit)
        )
        query_result = await self.db_session.execute(query_stmt)
        records = list(query_result.scalars().all())

        return records, total_count

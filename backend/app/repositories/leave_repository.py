"""
Leave repository layer.

Follows the workforce management repository conventions:
  - Takes an AsyncSession via __init__
  - Interacts with DB using SQLAlchemy 2.0 select queries
  - Performs flushes instead of commits (transaction boundary managed by service layer)
  - Uses joinedload/selectinload to eager-load relationships where appropriate
  - Includes overlap detection and balance management helpers
"""
from __future__ import annotations

from datetime import date
from typing import List, Optional, Tuple
from uuid import UUID

from sqlalchemy import and_, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.models.leave import LeaveBalance, LeaveRequest, LeaveStatus, LeaveType
from app.schemas.leave import LeaveBalanceCreate, LeaveBalanceUpdate, LeaveRequestUpdate


class LeaveRequestRepository:
    """Handles CRUD database operations for LeaveRequest records."""

    def __init__(self, db_session: AsyncSession) -> None:
        self.db_session = db_session

    async def create(
        self,
        employee_id: UUID,
        leave_type: LeaveType,
        start_date: date,
        end_date: date,
        total_days: int,
        reason: str,
    ) -> LeaveRequest:
        """Create a new leave request with PENDING status."""
        db_leave = LeaveRequest(
            employee_id=employee_id,
            leave_type=leave_type,
            start_date=start_date,
            end_date=end_date,
            total_days=total_days,
            reason=reason,
            status=LeaveStatus.PENDING,
        )
        self.db_session.add(db_leave)
        await self.db_session.flush()

        # Reload with relationships
        return await self.get_by_id(db_leave.id)  # type: ignore

    async def get_by_id(self, id: UUID) -> Optional[LeaveRequest]:
        """Fetch a single leave request by ID with employee and approver preloaded."""
        stmt = (
            select(LeaveRequest)
            .options(joinedload(LeaveRequest.employee), joinedload(LeaveRequest.approver))
            .where(LeaveRequest.id == id)
        )
        result = await self.db_session.execute(stmt)
        return result.scalar_one_or_none()

    async def update(self, db_obj: LeaveRequest, schema: LeaveRequestUpdate) -> LeaveRequest:
        """Update status / approver fields on an existing leave request."""
        update_data = schema.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(db_obj, key, value)

        self.db_session.add(db_obj)
        await self.db_session.flush()
        return await self.get_by_id(db_obj.id)  # type: ignore

    async def has_overlap(
        self,
        employee_id: UUID,
        start_date: date,
        end_date: date,
        exclude_id: Optional[UUID] = None,
    ) -> bool:
        """
        Return True if any non-cancelled leave request for the employee
        overlaps with the [start_date, end_date] range.

        Two date ranges [a, b] and [c, d] overlap when: a <= d AND c <= b.
        Cancelled requests are excluded from overlap checks.
        """
        stmt = select(func.count()).select_from(LeaveRequest).where(
            and_(
                LeaveRequest.employee_id == employee_id,
                LeaveRequest.status != LeaveStatus.CANCELLED,
                LeaveRequest.status != LeaveStatus.REJECTED,
                # Overlap condition
                LeaveRequest.start_date <= end_date,
                LeaveRequest.end_date >= start_date,
            )
        )
        if exclude_id:
            stmt = stmt.where(LeaveRequest.id != exclude_id)

        result = await self.db_session.execute(stmt)
        count = result.scalar_one()
        return count > 0

    async def list_paginated(
        self,
        employee_id: Optional[UUID] = None,
        status: Optional[LeaveStatus] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> Tuple[List[LeaveRequest], int]:
        """Fetch paginated leave requests with optional employee/status filters."""
        query_stmt = select(LeaveRequest).options(
            joinedload(LeaveRequest.employee),
            joinedload(LeaveRequest.approver),
        )
        count_stmt = select(func.count()).select_from(LeaveRequest)

        if employee_id:
            query_stmt = query_stmt.where(LeaveRequest.employee_id == employee_id)
            count_stmt = count_stmt.where(LeaveRequest.employee_id == employee_id)

        if status:
            query_stmt = query_stmt.where(LeaveRequest.status == status)
            count_stmt = count_stmt.where(LeaveRequest.status == status)

        # Count total
        count_result = await self.db_session.execute(count_stmt)
        total_count = count_result.scalar_one() or 0

        # Paginated and sorted query
        query_stmt = (
            query_stmt
            .order_by(LeaveRequest.start_date.desc(), LeaveRequest.created_at.desc())
            .offset(offset)
            .limit(limit)
        )
        query_result = await self.db_session.execute(query_stmt)
        records = list(query_result.scalars().all())

        return records, total_count


class LeaveBalanceRepository:
    """Handles CRUD database operations for LeaveBalance records."""

    def __init__(self, db_session: AsyncSession) -> None:
        self.db_session = db_session

    async def get_or_create(
        self,
        employee_id: UUID,
        leave_type: LeaveType,
        year: int,
    ) -> LeaveBalance:
        """
        Fetch the balance record for (employee, leave_type, year).
        Creates it with 0/0 allocation if it doesn't yet exist.
        """
        stmt = select(LeaveBalance).where(
            LeaveBalance.employee_id == employee_id,
            LeaveBalance.leave_type == leave_type,
            LeaveBalance.year == year,
        )
        result = await self.db_session.execute(stmt)
        balance = result.scalar_one_or_none()

        if balance is None:
            balance = LeaveBalance(
                employee_id=employee_id,
                leave_type=leave_type,
                year=year,
                allocated_days=0,
                used_days=0,
            )
            self.db_session.add(balance)
            await self.db_session.flush()

        return balance

    async def get_by_id(self, id: UUID) -> Optional[LeaveBalance]:
        """Fetch a balance record by UUID."""
        stmt = select(LeaveBalance).where(LeaveBalance.id == id)
        result = await self.db_session.execute(stmt)
        return result.scalar_one_or_none()

    async def create(self, schema: LeaveBalanceCreate) -> LeaveBalance:
        """Create or update the leave balance (upsert via get_or_create then set)."""
        balance = await self.get_or_create(
            schema.employee_id, schema.leave_type, schema.year
        )
        balance.allocated_days = schema.allocated_days
        self.db_session.add(balance)
        await self.db_session.flush()
        return balance

    async def update(self, db_obj: LeaveBalance, schema: LeaveBalanceUpdate) -> LeaveBalance:
        """Update allocated_days on an existing balance record."""
        db_obj.allocated_days = schema.allocated_days
        self.db_session.add(db_obj)
        await self.db_session.flush()
        return db_obj

    async def increment_used(self, employee_id: UUID, leave_type: LeaveType, year: int, days: int) -> None:
        """Increment used_days by the given amount (called on approve)."""
        balance = await self.get_or_create(employee_id, leave_type, year)
        balance.used_days = max(0, balance.used_days + days)
        self.db_session.add(balance)
        await self.db_session.flush()

    async def decrement_used(self, employee_id: UUID, leave_type: LeaveType, year: int, days: int) -> None:
        """Decrement used_days by the given amount (called on cancel/reject after approve)."""
        balance = await self.get_or_create(employee_id, leave_type, year)
        balance.used_days = max(0, balance.used_days - days)
        self.db_session.add(balance)
        await self.db_session.flush()

    async def list_for_employee(self, employee_id: UUID, year: Optional[int] = None) -> List[LeaveBalance]:
        """Fetch all balance entries for an employee, optionally filtered by year."""
        stmt = select(LeaveBalance).where(LeaveBalance.employee_id == employee_id)
        if year:
            stmt = stmt.where(LeaveBalance.year == year)
        stmt = stmt.order_by(LeaveBalance.year.desc(), LeaveBalance.leave_type)
        result = await self.db_session.execute(stmt)
        return list(result.scalars().all())

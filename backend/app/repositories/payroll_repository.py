from __future__ import annotations

from typing import List, Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.payroll import PayrollPeriod, PayrollRecord


class PayrollRepository:
    """Async repository for PayrollPeriod and PayrollRecord entities."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get_period_by_year_month(self, year: int, month: int) -> Optional[PayrollPeriod]:
        """Fetch payroll period by year and month."""
        stmt = (
            select(PayrollPeriod)
            .where(PayrollPeriod.year == year, PayrollPeriod.month == month)
            .options(selectinload(PayrollPeriod.records))
        )
        res = await self.db.execute(stmt)
        return res.scalar_one_or_none()

    async def get_period_by_id(self, id: UUID) -> Optional[PayrollPeriod]:
        """Fetch payroll period by UUID with records eagerly loaded."""
        stmt = (
            select(PayrollPeriod)
            .where(PayrollPeriod.id == id)
            .options(
                selectinload(PayrollPeriod.records).selectinload(PayrollRecord.employee)
            )
        )
        res = await self.db.execute(stmt)
        return res.scalar_one_or_none()

    async def list_periods(self, limit: int = 24, offset: int = 0) -> List[PayrollPeriod]:
        """Fetch list of historical payroll periods ordered newest first."""
        stmt = (
            select(PayrollPeriod)
            .order_by(PayrollPeriod.year.desc(), PayrollPeriod.month.desc())
            .offset(offset)
            .limit(limit)
        )
        res = await self.db.execute(stmt)
        return list(res.scalars().all())

    async def get_record_by_id(self, record_id: UUID) -> Optional[PayrollRecord]:
        """Fetch single employee payroll record by ID with employee and period loaded."""
        stmt = (
            select(PayrollRecord)
            .where(PayrollRecord.id == record_id)
            .options(
                selectinload(PayrollRecord.employee),
                selectinload(PayrollRecord.payroll_period)
            )
        )
        res = await self.db.execute(stmt)
        return res.scalar_one_or_none()

    async def create_period(self, period: PayrollPeriod) -> PayrollPeriod:
        """Add and flush a new PayrollPeriod."""
        self.db.add(period)
        await self.db.flush()
        return period

from __future__ import annotations

from typing import List, Optional, Tuple
from uuid import UUID
from datetime import datetime

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.audit_log import AuditLog
from app.models.user import User


class AuditLogRepository:
    """Async repository for querying immutable audit logs."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def list(
        self,
        action: Optional[str] = None,
        target_type: Optional[str] = None,
        user_id: Optional[UUID] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 50,
        offset: int = 0
    ) -> Tuple[List[AuditLog], int]:
        """Fetch audit log entries with optional filters, user eager loading, and total count."""
        stmt = select(AuditLog).options(selectinload(AuditLog.user))
        count_stmt = select(func.count(AuditLog.id))

        if action:
            stmt = stmt.where(AuditLog.action == action)
            count_stmt = count_stmt.where(AuditLog.action == action)
        if target_type:
            stmt = stmt.where(AuditLog.target_type == target_type)
            count_stmt = count_stmt.where(AuditLog.target_type == target_type)
        if user_id:
            stmt = stmt.where(AuditLog.user_id == user_id)
            count_stmt = count_stmt.where(AuditLog.user_id == user_id)
        if start_date:
            stmt = stmt.where(AuditLog.created_at >= start_date)
            count_stmt = count_stmt.where(AuditLog.created_at >= start_date)
        if end_date:
            stmt = stmt.where(AuditLog.created_at <= end_date)
            count_stmt = count_stmt.where(AuditLog.created_at <= end_date)

        # Count total matching
        total_res = await self.db.execute(count_stmt)
        total = total_res.scalar() or 0

        # Order by newest first & paginate
        stmt = stmt.order_by(AuditLog.created_at.desc()).offset(offset).limit(limit)
        res = await self.db.execute(stmt)
        items = list(res.scalars().all())

        return items, total

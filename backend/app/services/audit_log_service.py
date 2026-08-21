from __future__ import annotations

from datetime import datetime
from typing import Optional
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.audit_log_repository import AuditLogRepository
from app.schemas.audit_log import AuditLogListResponse, AuditLogResponse


class AuditLogService:
    """Service layer managing access to audit logs."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.repo = AuditLogRepository(db)

    async def get_audit_logs(
        self,
        action: Optional[str] = None,
        target_type: Optional[str] = None,
        user_id: Optional[UUID] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 50,
        offset: int = 0
    ) -> AuditLogListResponse:
        """Fetch audit log list enriched with operator email addresses."""
        items, total = await self.repo.list(
            action=action,
            target_type=target_type,
            user_id=user_id,
            start_date=start_date,
            end_date=end_date,
            limit=limit,
            offset=offset
        )

        response_items = []
        for log in items:
            response_items.append(
                AuditLogResponse(
                    id=log.id,
                    user_id=log.user_id,
                    user_email=log.user.email if log.user else None,
                    action=log.action,
                    target_type=log.target_type,
                    target_id=log.target_id,
                    details=log.details,
                    created_at=log.created_at
                )
            )

        return AuditLogListResponse(
            total=total,
            items=response_items,
            limit=limit,
            offset=offset
        )

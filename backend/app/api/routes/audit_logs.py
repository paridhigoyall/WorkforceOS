from __future__ import annotations

from datetime import datetime
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.api.dependencies.auth import get_current_user, require_role
from app.models.user import User, UserRole
from app.schemas.audit_log import AuditLogListResponse
from app.services.audit_log_service import AuditLogService

router = APIRouter(prefix="/audit-logs", tags=["Audit Logs"])


@router.get(
    "",
    response_model=AuditLogListResponse,
    status_code=status.HTTP_200_OK,
    summary="List system audit logs",
    description="Retrieve immutable system audit trail with filtering by action, target, user, or date range. Requires ADMIN or HR role."
)
async def list_audit_logs(
    action: Optional[str] = Query(None, description="Filter by action code (e.g. ONBOARD_EMPLOYEE)"),
    target_type: Optional[str] = Query(None, description="Filter by target table name (e.g. employees)"),
    user_id: Optional[UUID] = Query(None, description="Filter by operator user UUID"),
    start_date: Optional[datetime] = Query(None, description="Filter logs starting from datetime"),
    end_date: Optional[datetime] = Query(None, description="Filter logs up to datetime"),
    limit: int = Query(50, ge=1, le=200, description="Page limit"),
    offset: int = Query(0, ge=0, description="Page offset"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role([UserRole.ADMIN, UserRole.HR]))
) -> AuditLogListResponse:
    """Endpoint for retrieving system audit logs."""
    service = AuditLogService(db)
    return await service.get_audit_logs(
        action=action,
        target_type=target_type,
        user_id=user_id,
        start_date=start_date,
        end_date=end_date,
        limit=limit,
        offset=offset
    )

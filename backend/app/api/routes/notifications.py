from __future__ import annotations

from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies.auth import get_current_user
from app.core.database import get_db
from app.models.notification import NotificationType
from app.models.user import User
from app.schemas.notification import NotificationResponse, NotificationUnreadCountResponse
from app.services.notification_service import NotificationService

router = APIRouter(prefix="/notifications", tags=["Notifications"])


@router.get(
    "/",
    response_model=List[NotificationResponse],
    summary="List current user notifications",
    description="Fetch paginated in-app notifications with optional unread and category filters.",
)
async def list_notifications(
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    unread_only: bool = Query(False),
    type: Optional[NotificationType] = Query(None),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = NotificationService(db)
    return await service.get_user_notifications(
        user_id=current_user.id,
        limit=limit,
        offset=offset,
        unread_only=unread_only,
        type_filter=type,
    )


@router.get(
    "/unread-count",
    response_model=NotificationUnreadCountResponse,
    summary="Get unread notification count",
    description="Returns the total count of unacknowledged notifications for the top navigation badge.",
)
async def get_unread_count(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = NotificationService(db)
    return await service.get_unread_count(current_user.id)


@router.put(
    "/{notification_id}/read",
    response_model=NotificationResponse,
    summary="Mark notification as read",
    description="Updates a single notification status to read.",
)
async def mark_as_read(
    notification_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = NotificationService(db)
    try:
        return await service.mark_read(notification_id, current_user.id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.put(
    "/read-all",
    summary="Mark all notifications as read",
    description="Marks all unread notifications for current user as acknowledged.",
)
async def mark_all_as_read(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = NotificationService(db)
    count = await service.mark_all_read(current_user.id)
    return {"status": "success", "marked_read_count": count}

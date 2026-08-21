from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, Optional
from uuid import UUID
from pydantic import BaseModel, ConfigDict


class AuditLogResponse(BaseModel):
    """Response schema for an audit log entry."""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    user_id: UUID
    user_email: Optional[str] = None
    action: str
    target_type: str
    target_id: UUID
    details: Optional[Dict[str, Any]] = None
    created_at: datetime


class AuditLogListResponse(BaseModel):
    """Paginated list response for audit logs."""
    total: int
    items: list[AuditLogResponse]
    limit: int
    offset: int

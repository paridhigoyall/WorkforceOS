"""
Pydantic schemas for Leave endpoints.

Follows project validation conventions:
  - Field(...) with descriptions
  - ConfigDict(from_attributes=True) for response serialization
  - computed_field for calculated runtime fields like remaining_days
"""
from __future__ import annotations

from datetime import date, datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, computed_field, model_validator

from app.models.leave import LeaveStatus, LeaveType


# ---------------------------------------------------------------------------
# Leave Request Schemas
# ---------------------------------------------------------------------------

class LeaveRequestBase(BaseModel):
    """Base schema shared by create and response."""

    leave_type: LeaveType = Field(..., description="Type of leave (Casual, Sick, Earned, Unpaid)")
    start_date: date = Field(..., description="Start date of the leave period")
    end_date: date = Field(..., description="End date of the leave period (inclusive)")
    reason: str = Field(..., min_length=5, max_length=255, description="Reason for the leave request")


class LeaveRequestCreate(LeaveRequestBase):
    """Payload for POST /leave — apply for leave."""

    # Admin/HR can submit on behalf of another employee; Staff defaults to self
    employee_id: Optional[UUID] = Field(
        None,
        description="UUID of the employee (Admin/HR only; defaults to current user's employee profile)"
    )

    @model_validator(mode="after")
    def validate_dates(self) -> "LeaveRequestCreate":
        if self.end_date < self.start_date:
            raise ValueError("end_date must be on or after start_date")
        return self


class LeaveRequestUpdate(BaseModel):
    """Internal schema used by the repository update path."""

    status: Optional[LeaveStatus] = Field(None, description="Updated status")
    approved_by: Optional[UUID] = Field(None, description="UUID of the approver")
    approved_at: Optional[datetime] = Field(None, description="Timestamp of decision")


class LeaveRequestResponse(LeaveRequestBase):
    """Response schema serializing leave request records."""

    id: UUID
    employee_id: UUID
    total_days: int
    status: LeaveStatus
    approved_by: Optional[UUID]
    approved_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ---------------------------------------------------------------------------
# Leave Balance Schemas
# ---------------------------------------------------------------------------

class LeaveBalanceCreate(BaseModel):
    """Schema for allocating leave balance (Admin/HR only)."""

    employee_id: UUID = Field(..., description="UUID of the employee")
    leave_type: LeaveType = Field(..., description="Type of leave to allocate")
    year: int = Field(..., ge=2000, le=2100, description="Calendar year for the balance")
    allocated_days: int = Field(..., ge=0, le=365, description="Number of days to allocate")


class LeaveBalanceUpdate(BaseModel):
    """Schema for adjusting allocated days on an existing balance record."""

    allocated_days: int = Field(..., ge=0, le=365, description="Updated total allocated days")


class LeaveBalanceResponse(BaseModel):
    """Response schema serializing leave balance records."""

    id: UUID
    employee_id: UUID
    leave_type: LeaveType
    year: int
    allocated_days: int
    used_days: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

    @computed_field
    @property
    def remaining_days(self) -> int:
        """Days still available (allocated - used), floored at 0."""
        return max(0, self.allocated_days - self.used_days)

"""
Pydantic schemas for Attendance endpoints.

Follows project validation conventions:
 - Field(...) with descriptions
 - ConfigDict(from_attributes=True) for response serialization
 - computed_field for calculated runtime fields like overtime_hours
"""
from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, computed_field

from app.models.attendance import AttendanceStatus


class AttendanceBase(BaseModel):
    """Base schema for attendance data."""

    employee_id: UUID = Field(..., description="UUID of the employee")
    attendance_date: date = Field(..., description="The date of the attendance record")
    attendance_status: AttendanceStatus = Field(
        ..., description="Daily status (e.g. Present, Absent, Half-Day, Late)"
    )


class AttendanceCreate(AttendanceBase):
    """Schema for recording a check-in."""

    check_in_time: datetime = Field(..., description="Timestamp when the employee checked in")


class CheckInRequest(BaseModel):
    """Payload for POST /attendance/check-in."""

    employee_id: Optional[UUID] = Field(
        None, description="UUID of the employee (admin/hr only, defaults to current user's employee profile)"
    )
    check_in_time: Optional[datetime] = Field(
        None, description="Optional custom check-in time (defaults to current time)"
    )


class CheckOutRequest(BaseModel):
    """Payload for POST /attendance/check-out or POST /attendance/{id}/check-out."""

    check_out_time: Optional[datetime] = Field(
        None, description="Optional custom check-out time (defaults to current time)"
    )
    employee_id: Optional[UUID] = Field(
        None, description="Employee UUID (Admin/HR only — omit to use current user's active record)"
    )


class AttendanceUpdate(BaseModel):
    """Schema for updating an attendance record (e.g. on check-out)."""

    check_out_time: Optional[datetime] = Field(None, description="Timestamp when the employee checked out")
    total_hours: Optional[Decimal] = Field(
        None,
        ge=0,
        max_digits=5,
        decimal_places=2,
        description="Total hours worked for the day"
    )
    attendance_status: Optional[AttendanceStatus] = Field(None, description="Updated status")


class AttendanceResponse(AttendanceBase):
    """Response schema serializing attendance records."""

    id: UUID
    check_in_time: datetime
    check_out_time: Optional[datetime]
    total_hours: Decimal
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

    @computed_field
    @property
    def overtime_hours(self) -> Decimal:
        """Calculate overtime hours (hours worked in excess of 8.00)."""
        if self.total_hours > Decimal("8.00"):
            return self.total_hours - Decimal("8.00")
        return Decimal("0.00")

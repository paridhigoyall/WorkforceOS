"""
Attendance service layer.

Follows workforce management conventions:
  - Takes an AsyncSession via __init__ and instantiates repositories
  - Encapsulates database transactions inside 'async with self.db_session.begin():' blocks
  - Raises ValueError on validation / business logic failures
  - Writes audit logs for write operations (check-in, check-out)
"""
from __future__ import annotations

from datetime import date, datetime, time, timezone
from decimal import Decimal
from typing import List, Optional, Tuple
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.attendance import Attendance, AttendanceStatus
from app.models.audit_log import AuditLog
from app.models.employee import Employee
from app.repositories.attendance_repository import AttendanceRepository
from app.schemas.attendance import AttendanceCreate, AttendanceUpdate


class AttendanceService:
    """Service layer coordinating business rules for employee Attendance records."""

    def __init__(self, db_session: AsyncSession) -> None:
        self.db_session = db_session
        self.repo = AttendanceRepository(db_session)

    async def check_in(self, employee_id: UUID, check_in_time: Optional[datetime] = None) -> Attendance:
        """
        Record check-in for an employee.

        Rules:
          - Employee must exist and not be soft-deleted.
          - Only one check-in allowed per employee per day.
          - Late arrivals (check-in after 09:00:00) get marked as LATE.
        """
        async with self.db_session.begin():
            # 1. Validate employee existence
            emp_stmt = select(Employee).where(
                Employee.id == employee_id,
                Employee.is_deleted == False  # noqa: E712
            )
            emp_result = await self.db_session.execute(emp_stmt)
            employee = emp_result.scalar_one_or_none()
            if not employee:
                raise ValueError(f"Cannot check in: Employee with ID {employee_id} does not exist.")

            # 2. Establish timezone-aware check-in time and date
            if check_in_time is None:
                check_in_time = datetime.now(timezone.utc)
            elif check_in_time.tzinfo is None:
                check_in_time = check_in_time.replace(tzinfo=timezone.utc)

            attendance_date = check_in_time.date()

            # 3. Prevent duplicate check-ins for the day
            existing = await self.repo.get_by_employee_and_date(employee_id, attendance_date)
            if existing:
                raise ValueError(
                    f"Employee {employee_id} has already checked in for today ({attendance_date})."
                )

            # 4. Determine daily status (check-in cutoff at 09:00:00)
            late_threshold = time(9, 0, 0)
            if check_in_time.time() > late_threshold:
                status = AttendanceStatus.LATE
            else:
                status = AttendanceStatus.PRESENT

            # 5. Create the record
            schema = AttendanceCreate(
                employee_id=employee_id,
                attendance_date=attendance_date,
                check_in_time=check_in_time,
                attendance_status=status,
            )
            db_attendance = await self.repo.create(schema)

            # 6. Log the audit event
            audit_log = AuditLog(
                user_id=employee.user_id,
                action="EMPLOYEE_CHECK_IN",
                target_type="attendances",
                target_id=db_attendance.id,
                details={
                    "employee_id": str(employee_id),
                    "attendance_date": str(attendance_date),
                    "check_in_time": check_in_time.isoformat(),
                    "status": status.value,
                },
            )
            self.db_session.add(audit_log)

        return db_attendance

    async def check_out(self, attendance_id: UUID, check_out_time: Optional[datetime] = None) -> Attendance:
        """
        Record check-out for an employee's existing attendance record.

        Rules:
          - Attendance record must exist.
          - Employee must not have already checked out.
          - Check-out time must be chronologically after the check-in time.
          - Calculates total hours worked.
          - Calculates overtime hours (if total hours > 8).
          - Sets status to HALF_DAY if total hours worked < 4.
        """
        async with self.db_session.begin():
            # Fetch target record inside transaction
            db_attendance = await self.repo.get_by_id(attendance_id)
            if not db_attendance:
                raise ValueError(f"Attendance record with ID {attendance_id} not found.")

            if db_attendance.check_out_time is not None:
                raise ValueError("Employee has already checked out for this attendance record.")
            # Establish timezone-aware check-out time
            if check_out_time is None:
                check_out_time = datetime.now(timezone.utc)
            elif check_out_time.tzinfo is None:
                check_out_time = check_out_time.replace(tzinfo=timezone.utc)

            # Validate date sequence
            if check_out_time <= db_attendance.check_in_time:
                raise ValueError("Check-out time must be chronologically after check-in time.")

            # Calculate worked hours
            duration = check_out_time - db_attendance.check_in_time
            total_hours = Decimal(f"{duration.total_seconds() / 3600.0:.2f}")

            # Assign status based on total hours worked
            status = db_attendance.attendance_status
            if total_hours < Decimal("4.00"):
                status = AttendanceStatus.HALF_DAY

            # Update the attendance record
            schema = AttendanceUpdate(
                check_out_time=check_out_time,
                total_hours=total_hours,
                attendance_status=status,
            )
            db_attendance = await self.repo.update(db_attendance, schema)

            # Fetch the associated employee's user ID for the audit log
            employee = db_attendance.employee
            
            # Calculate overtime for the audit log
            overtime_hours = max(Decimal("0.00"), total_hours - Decimal("8.00"))

            # Log the audit event
            audit_log = AuditLog(
                user_id=employee.user_id,
                action="EMPLOYEE_CHECK_OUT",
                target_type="attendances",
                target_id=db_attendance.id,
                details={
                    "employee_id": str(db_attendance.employee_id),
                    "attendance_date": str(db_attendance.attendance_date),
                    "check_out_time": check_out_time.isoformat(),
                    "total_hours": float(total_hours),
                    "overtime_hours": float(overtime_hours),
                    "status": status.value,
                },
            )
            self.db_session.add(audit_log)

        return db_attendance

    async def get_attendance(self, id: UUID) -> Attendance:
        """Fetch attendance record by ID, raising error if missing."""
        db_attendance = await self.repo.get_by_id(id)
        if not db_attendance:
            raise ValueError(f"Attendance record with ID {id} not found.")
        return db_attendance

    async def list_attendance(
        self,
        employee_id: Optional[UUID] = None,
        limit: int = 100,
        offset: int = 0
    ) -> Tuple[List[Attendance], int]:
        """Fetch paginated attendance records, optionally filtered by employee."""
        return await self.repo.list_paginated(
            employee_id=employee_id,
            limit=limit,
            offset=offset
        )

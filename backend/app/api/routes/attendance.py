"""
FastAPI router for Attendance endpoints.

Mounts under `/api/attendance` prefix.
Authorisation rules:
  - Admin & HR roles can view/manage attendance for all employees.
  - Staff role can only view/manage their own attendance records.
"""
from __future__ import annotations

from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies.auth import get_current_user
from app.core.database import get_db
from app.models.user import User, UserRole
from app.repositories.employee_repository import EmployeeRepository
from app.schemas.attendance import (
    AttendanceResponse,
    CheckInRequest,
    CheckOutRequest,
)
from app.services.attendance_service import AttendanceService

router = APIRouter(prefix="/attendance", tags=["Attendance"])


async def get_employee_for_user(db: AsyncSession, user_id: UUID):
    """Helper to retrieve active employee profile for a user ID."""
    emp_repo = EmployeeRepository(db)
    employee = await emp_repo.get_by_user_id(user_id)
    if not employee:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current user does not have an active employee profile."
        )
    return employee


@router.post(
    "/check-in",
    response_model=AttendanceResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Record a check-in",
    description="Creates a daily attendance check-in record for an employee."
)
async def check_in(
    payload: CheckInRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    service = AttendanceService(db)
    is_privileged = current_user.role in (UserRole.ADMIN, UserRole.HR)

    if payload.employee_id is not None:
        # If specifying an employee_id, must be Admin/HR
        if not is_privileged:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access forbidden: Only Administrators or HR can record check-in for other employees."
            )
        employee_id = payload.employee_id
    else:
        # Default to the current user's employee profile
        employee = await get_employee_for_user(db, current_user.id)
        employee_id = employee.id

    try:
        return await service.check_in(employee_id, payload.check_in_time)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post(
    "/check-out",
    response_model=AttendanceResponse,
    summary="Record a check-out for active attendance",
    description="Updates the active open attendance check-in record for an employee with a check-out time."
)
async def check_out_current(
    payload: Optional[CheckOutRequest] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    service = AttendanceService(db)
    is_privileged = current_user.role in (UserRole.ADMIN, UserRole.HR)

    if payload and payload.employee_id is not None:
        if not is_privileged:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access forbidden: Only Administrators or HR can record check-out for other employees."
            )
        employee_id = payload.employee_id
    else:
        employee = await get_employee_for_user(db, current_user.id)
        employee_id = employee.id

    check_out_time = payload.check_out_time if payload else None

    try:
        return await service.check_out_active(employee_id, check_out_time)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post(
    "/{id}/check-out",
    response_model=AttendanceResponse,
    summary="Record a check-out",
    description="Updates an existing attendance check-in record with a check-out time."
)
async def check_out(
    id: UUID,
    payload: CheckOutRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    service = AttendanceService(db)
    is_privileged = current_user.role in (UserRole.ADMIN, UserRole.HR)

    try:
        attendance = await service.get_attendance(id)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )

    # Check authorization: Admin/HR or self check-out
    if not is_privileged:
        employee = await get_employee_for_user(db, current_user.id)
        if attendance.employee_id != employee.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access forbidden: You cannot modify attendance records of other employees."
            )

    try:
        return await service.check_out(id, payload.check_out_time)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get(
    "/{id}",
    response_model=AttendanceResponse,
    summary="Get attendance details",
    description="Retrieve specific attendance record details."
)
async def get_attendance(
    id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    service = AttendanceService(db)
    is_privileged = current_user.role in (UserRole.ADMIN, UserRole.HR)

    try:
        attendance = await service.get_attendance(id)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )

    # Check authorization: Admin/HR or self record
    if not is_privileged:
        employee = await get_employee_for_user(db, current_user.id)
        if attendance.employee_id != employee.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access forbidden: You do not have permission to view this attendance record."
            )

    return attendance


@router.get(
    "/",
    response_model=List[AttendanceResponse],
    summary="List attendance records",
    description="Retrieve paginated attendance records, filtered by employee."
)
async def list_attendance(
    employee_id: Optional[UUID] = Query(None, description="Filter by employee UUID"),
    limit: int = Query(10, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    service = AttendanceService(db)
    is_privileged = current_user.role in (UserRole.ADMIN, UserRole.HR)

    if not is_privileged:
        # Non-privileged users must only access their own records
        employee = await get_employee_for_user(db, current_user.id)
        if employee_id is not None and employee_id != employee.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access forbidden: You cannot view attendance records of other employees."
            )
        employee_id = employee.id

    records, _ = await service.list_attendance(
        employee_id=employee_id,
        limit=limit,
        offset=offset
    )
    return records

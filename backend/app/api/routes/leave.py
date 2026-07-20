"""
FastAPI router for Leave endpoints.

Mounts under `/api/leave` prefix.
Authorisation rules:
  - Admin & HR can view/manage leave for all employees and approve/reject.
  - Staff can only apply, view, and cancel their own leave requests.
  - Only Admin & HR can allocate or update leave balances.
  - Staff can view their own balances.
"""
from __future__ import annotations

from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies.auth import get_current_user, require_role
from app.core.database import get_db
from app.models.leave import LeaveStatus
from app.models.user import User, UserRole
from app.repositories.employee_repository import EmployeeRepository
from app.schemas.leave import (
    LeaveBalanceCreate,
    LeaveBalanceResponse,
    LeaveBalanceUpdate,
    LeaveRequestCreate,
    LeaveRequestResponse,
)
from app.services.leave_service import LeaveService

router = APIRouter(prefix="/leave", tags=["Leave"])


# ---------------------------------------------------------------------------
# Helper — resolve the current user's employee profile
# ---------------------------------------------------------------------------

async def get_employee_for_user(db: AsyncSession, user_id: UUID):
    """Helper to retrieve active employee profile for a user ID."""
    emp_repo = EmployeeRepository(db)
    employee = await emp_repo.get_by_user_id(user_id)
    if not employee:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current user does not have an active employee profile.",
        )
    return employee


# ===========================================================================
# Leave Request Endpoints
# ===========================================================================

@router.post(
    "/",
    response_model=LeaveRequestResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Apply for leave",
    description=(
        "Submit a new leave request. "
        "Admin/HR may specify any employee_id; Staff defaults to their own profile."
    ),
)
async def apply_leave(
    payload: LeaveRequestCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = LeaveService(db)
    is_privileged = current_user.role in (UserRole.ADMIN, UserRole.HR)

    if payload.employee_id is not None:
        # Admin/HR can file on behalf of another employee
        if not is_privileged:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access forbidden: Only Administrators or HR can apply leave for other employees.",
            )
        employee_id = payload.employee_id
    else:
        # Staff self-service: resolve their own employee profile
        employee = await get_employee_for_user(db, current_user.id)
        employee_id = employee.id

    # Inject resolved employee_id into payload
    resolved_payload = payload.model_copy(update={"employee_id": employee_id})

    try:
        return await service.apply(resolved_payload, requesting_user_id=current_user.id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))


@router.get(
    "/",
    response_model=List[LeaveRequestResponse],
    summary="List leave requests",
    description="Retrieve paginated leave requests, optionally filtered by employee or status.",
)
async def list_leave_requests(
    employee_id: Optional[UUID] = Query(None, description="Filter by employee UUID"),
    status_filter: Optional[LeaveStatus] = Query(None, alias="status", description="Filter by status"),
    limit: int = Query(10, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = LeaveService(db)
    is_privileged = current_user.role in (UserRole.ADMIN, UserRole.HR)

    if not is_privileged:
        # Staff may only view their own records
        employee = await get_employee_for_user(db, current_user.id)
        if employee_id is not None and employee_id != employee.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access forbidden: You cannot view leave records of other employees.",
            )
        employee_id = employee.id

    records, _ = await service.list_leaves(
        employee_id=employee_id,
        status=status_filter,
        limit=limit,
        offset=offset,
    )
    return records


@router.get(
    "/{id}",
    response_model=LeaveRequestResponse,
    summary="Get leave request details",
    description="Retrieve a specific leave request by ID.",
)
async def get_leave_request(
    id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = LeaveService(db)
    is_privileged = current_user.role in (UserRole.ADMIN, UserRole.HR)

    try:
        leave = await service.get_leave(id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))

    if not is_privileged:
        employee = await get_employee_for_user(db, current_user.id)
        if leave.employee_id != employee.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access forbidden: You do not have permission to view this leave request.",
            )

    return leave


@router.post(
    "/{id}/approve",
    response_model=LeaveRequestResponse,
    summary="Approve a leave request",
    description="Approve a PENDING leave request. Admin and HR only.",
)
async def approve_leave(
    id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role([UserRole.ADMIN, UserRole.HR])),
):
    service = LeaveService(db)
    try:
        return await service.approve(id, approver_user_id=current_user.id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))


@router.post(
    "/{id}/reject",
    response_model=LeaveRequestResponse,
    summary="Reject a leave request",
    description="Reject a PENDING leave request. Admin and HR only.",
)
async def reject_leave(
    id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role([UserRole.ADMIN, UserRole.HR])),
):
    service = LeaveService(db)
    try:
        return await service.reject(id, approver_user_id=current_user.id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))


@router.post(
    "/{id}/cancel",
    response_model=LeaveRequestResponse,
    summary="Cancel a leave request",
    description=(
        "Cancel a leave request. "
        "Staff may only cancel their own requests; Admin/HR may cancel any."
    ),
)
async def cancel_leave(
    id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = LeaveService(db)
    is_privileged = current_user.role in (UserRole.ADMIN, UserRole.HR)

    try:
        leave = await service.get_leave(id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))

    if not is_privileged:
        employee = await get_employee_for_user(db, current_user.id)
        if leave.employee_id != employee.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access forbidden: You can only cancel your own leave requests.",
            )

    try:
        return await service.cancel(id, requesting_user_id=current_user.id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))


# ===========================================================================
# Leave Balance Endpoints
# ===========================================================================

@router.post(
    "/balances/",
    response_model=LeaveBalanceResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Allocate leave balance",
    description="Set or overwrite leave allocation for an employee. Admin and HR only.",
)
async def allocate_balance(
    payload: LeaveBalanceCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role([UserRole.ADMIN, UserRole.HR])),
):
    service = LeaveService(db)
    try:
        return await service.allocate_balance(payload, requesting_user_id=current_user.id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))


@router.put(
    "/balances/{balance_id}",
    response_model=LeaveBalanceResponse,
    summary="Update leave balance allocation",
    description="Adjust the allocated_days on an existing balance entry. Admin and HR only.",
)
async def update_balance(
    balance_id: UUID,
    payload: LeaveBalanceUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role([UserRole.ADMIN, UserRole.HR])),
):
    service = LeaveService(db)
    try:
        return await service.update_balance(balance_id, payload, requesting_user_id=current_user.id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))


@router.get(
    "/balances/{employee_id}",
    response_model=List[LeaveBalanceResponse],
    summary="Get leave balances for an employee",
    description=(
        "Retrieve all leave balance entries for an employee. "
        "Staff may only view their own; Admin/HR may view any."
    ),
)
async def get_employee_balances(
    employee_id: UUID,
    year: Optional[int] = Query(None, ge=2000, le=2100, description="Filter by calendar year"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = LeaveService(db)
    is_privileged = current_user.role in (UserRole.ADMIN, UserRole.HR)

    if not is_privileged:
        employee = await get_employee_for_user(db, current_user.id)
        if employee.id != employee_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access forbidden: You can only view your own leave balances.",
            )

    return await service.list_balances(employee_id, year)

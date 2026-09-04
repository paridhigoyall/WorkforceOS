from __future__ import annotations

from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.api.dependencies.auth import get_current_user, require_role
from app.models.user import User, UserRole
from app.repositories.employee_repository import EmployeeRepository
from app.schemas.payroll import (
    PayrollGenerationRequest,
    PayrollPeriodResponse,
    PayslipDetailResponse
)
from app.services.payroll_service import PayrollService

router = APIRouter(prefix="/payroll", tags=["Payroll"])


@router.post(
    "/generate",
    response_model=PayrollPeriodResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Generate monthly payroll batch",
    description="Calculates gross pay, overtime earnings, unpaid leave deductions, and net pay for all active employees. Requires ADMIN or HR role."
)
async def generate_payroll(
    payload: PayrollGenerationRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role([UserRole.ADMIN, UserRole.HR]))
) -> PayrollPeriodResponse:
    """Generate or recalculate monthly payroll."""
    service = PayrollService(db)
    try:
        return await service.generate_monthly_payroll(payload, operator_id=current_user.id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get(
    "/periods",
    response_model=List[PayrollPeriodResponse],
    status_code=status.HTTP_200_OK,
    summary="List historical payroll periods",
    description="Retrieve all processed payroll batches. Requires ADMIN or HR role."
)
async def list_payroll_periods(
    limit: int = Query(24, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role([UserRole.ADMIN, UserRole.HR]))
) -> List[PayrollPeriodResponse]:
    """List payroll periods."""
    service = PayrollService(db)
    return await service.list_periods(limit=limit, offset=offset)


@router.get(
    "/periods/{period_id}",
    response_model=PayrollPeriodResponse,
    status_code=status.HTTP_200_OK,
    summary="Get payroll period details",
    description="Fetch a specific payroll batch and its employee payslip records. Requires ADMIN or HR role."
)
async def get_payroll_period(
    period_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role([UserRole.ADMIN, UserRole.HR]))
) -> PayrollPeriodResponse:
    """Get payroll period details."""
    service = PayrollService(db)
    try:
        return await service.get_period(period_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.post(
    "/periods/{period_id}/approve",
    response_model=PayrollPeriodResponse,
    status_code=status.HTTP_200_OK,
    summary="Approve payroll batch",
    description="Approve a draft payroll period and transition all records to PAID status. Requires ADMIN role."
)
async def approve_payroll_period(
    period_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role([UserRole.ADMIN]))
) -> PayrollPeriodResponse:
    """Approve payroll period."""
    service = PayrollService(db)
    try:
        return await service.approve_period(period_id, operator_id=current_user.id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get(
    "/records/{record_id}/payslip",
    response_model=PayslipDetailResponse,
    status_code=status.HTTP_200_OK,
    summary="Get employee digital payslip",
    description="Retrieve printable digital payslip for an individual employee record."
)
async def get_employee_payslip(
    record_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> PayslipDetailResponse:
    """Get employee printable digital payslip."""
    service = PayrollService(db)
    try:
        return await service.get_payslip(record_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.get(
    "/payslips/my",
    response_model=List[PayslipDetailResponse],
    status_code=status.HTTP_200_OK,
    summary="Get my payslips",
    description="Retrieve all payslips for the currently authenticated employee, newest first. Staff can only see their own."
)
async def get_my_payslips(
    limit: int = Query(12, ge=1, le=50),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> List[PayslipDetailResponse]:
    """Return all payslips for the currently authenticated employee."""
    emp_repo = EmployeeRepository(db)
    employee = await emp_repo.get_by_user_id(current_user.id)
    if not employee:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current user does not have an active employee profile."
        )
    service = PayrollService(db)
    return await service.get_my_payslips(employee.id, limit=limit, offset=offset)

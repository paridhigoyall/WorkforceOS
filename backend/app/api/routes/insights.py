from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies.auth import get_current_user, require_role
from app.core.database import get_db
from app.models.user import User, UserRole
from app.schemas.insights import (
    AttendanceInsights,
    LeaveInsights,
    DepartmentInsights,
    AIPredictionDataset,
)
from app.services.insights_service import InsightsService

router = APIRouter(prefix="/insights", tags=["Insights"])


@router.get(
    "/attendance",
    response_model=AttendanceInsights,
    summary="Get attendance insights",
    description="Calculate overall attendance, late rate, and overtime hours. Admin and HR only.",
)
async def get_attendance_insights(
    employee_id: Optional[UUID] = Query(None, description="Filter by a specific employee"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role([UserRole.ADMIN, UserRole.HR])),
):
    service = InsightsService(db)
    return await service.get_attendance_insights(employee_id)


@router.get(
    "/leave",
    response_model=LeaveInsights,
    summary="Get leave insights",
    description="Calculate total leave requests, approved days, and leave balance utilization. Admin and HR only.",
)
async def get_leave_insights(
    employee_id: Optional[UUID] = Query(None, description="Filter by a specific employee"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role([UserRole.ADMIN, UserRole.HR])),
):
    service = InsightsService(db)
    return await service.get_leave_insights(employee_id)


@router.get(
    "/departments",
    response_model=List[DepartmentInsights],
    summary="Get department payroll and attendance insights",
    description="Aggregate headcount, total monthly payroll, and performance stats per department. Admin and HR only.",
)
async def get_department_insights(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role([UserRole.ADMIN, UserRole.HR])),
):
    service = InsightsService(db)
    return await service.get_department_insights()


@router.get(
    "/ai-dataset",
    response_model=AIPredictionDataset,
    summary="Generate AI prediction features",
    description="Retrieve structured historical data and anomaly flags for machine learning. Admin only.",
)
async def get_ai_prediction_dataset(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role([UserRole.ADMIN])),
):
    service = InsightsService(db)
    return await service.get_ai_prediction_dataset()

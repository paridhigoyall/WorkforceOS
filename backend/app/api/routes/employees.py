from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.api.dependencies.auth import get_current_user
from app.models.user import User
from app.schemas.employee import EmployeeCreate, EmployeeUpdate, EmployeeResponse
from app.services.employee_service import EmployeeService

router = APIRouter(prefix="/employees", tags=["Employees"])


# Auth helper to verify admin role
def require_admin(current_user: User = Depends(get_current_user)) -> User:
    if not hasattr(current_user, "role") or getattr(current_user, "role") != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access forbidden: Admin privilege required."
        )
    return current_user


@router.post(
    "/onboard",
    response_model=EmployeeResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Onboard a new employee",
    description="Creates an employee profile associated with an existing user. Admin only."
)
async def onboard_employee(
    schema: EmployeeCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    service = EmployeeService(db)
    try:
        # Pass current_user.id as the operator_id for audit logging
        return await service.onboard_employee(schema, operator_id=current_user.id)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get(
    "/",
    response_model=List[EmployeeResponse],
    summary="List employees",
    description="Retrieve a paginated list of employee profiles. Admin only."
)
async def list_employees(
    department_id: Optional[UUID] = Query(None, description="Filter by department UUID"),
    limit: int = Query(10, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin)
):
    service = EmployeeService(db)
    records, _ = await service.list_employees(
        department_id=department_id,
        limit=limit,
        offset=offset
    )
    return records


@router.get(
    "/{id}",
    response_model=EmployeeResponse,
    summary="Get employee profile",
    description="Retrieve an employee profile by ID. Restricted to the profile owner or an Admin."
)
async def get_employee(
    id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    service = EmployeeService(db)
    try:
        db_emp = await service.get_employee(id)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
        
    # Owner/Admin authorization check
    is_admin = getattr(current_user, "role", None) == "admin"
    is_owner = db_emp.user_id == current_user.id
    if not (is_admin or is_owner):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access forbidden: You do not have permission to view this profile."
        )
        
    return db_emp


@router.put(
    "/{id}",
    response_model=EmployeeResponse,
    summary="Update employee details",
    description="Update employee parameters. Restricted to the profile owner or an Admin."
)
async def update_employee(
    id: UUID,
    schema: EmployeeUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    service = EmployeeService(db)
    try:
        db_emp = await service.get_employee(id)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )

    # Owner/Admin authorization check
    is_admin = getattr(current_user, "role", None) == "admin"
    is_owner = db_emp.user_id == current_user.id
    if not (is_admin or is_owner):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access forbidden: You do not have permission to modify this profile."
        )

    # Business rule: Non-admins cannot update base salary
    if schema.base_salary is not None and not is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access forbidden: Only Administrators can modify employee base salary."
        )

    try:
        return await service.update_employee(id, schema, operator_id=current_user.id)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.delete(
    "/{id}",
    response_model=EmployeeResponse,
    summary="Offboard employee",
    description="Soft-deletes employee profile and triggers offboarding audits. Admin only."
)
async def offboard_employee(
    id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    service = EmployeeService(db)
    try:
        return await service.offboard_employee(id, operator_id=current_user.id)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )

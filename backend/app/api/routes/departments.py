from typing import List, Tuple
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.api.dependencies.auth import get_current_user
from app.models.user import User  # Assuming User model has a 'role' field
from app.schemas.department import DepartmentCreate, DepartmentUpdate, DepartmentResponse
from app.services.department_service import DepartmentService

router = APIRouter(prefix="/departments", tags=["Departments"])


# Admin privilege verification dependency
def require_admin(current_user: User = Depends(get_current_user)) -> User:
    # Check if the user has admin role (adjust attribute names as per your User model schema)
    if not hasattr(current_user, "role") or getattr(current_user, "role") != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access forbidden: Admin role is required to perform this action."
        )
    return current_user


@router.post(
    "/",
    response_model=DepartmentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new department",
    description="Registers a new department. Admin role is required."
)
async def create_department(
    schema: DepartmentCreate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin)
):
    service = DepartmentService(db)
    try:
        return await service.create_department(schema)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get(
    "/",
    response_model=List[DepartmentResponse],
    summary="List departments",
    description="Fetch a paginated list of active departments. Authenticated users only."
)
async def list_departments(
    limit: int = Query(10, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user)
):
    service = DepartmentService(db)
    records, _ = await service.list_departments(limit=limit, offset=offset)
    return records


@router.get(
    "/{id}",
    response_model=DepartmentResponse,
    summary="Get department details",
    description="Retrieve a department by its unique ID. Authenticated users only."
)
async def get_department(
    id: UUID,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user)
):
    service = DepartmentService(db)
    try:
        return await service.get_department(id)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


@router.put(
    "/{id}",
    response_model=DepartmentResponse,
    summary="Update a department",
    description="Update a department's details. Admin role is required."
)
async def update_department(
    id: UUID,
    schema: DepartmentUpdate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin)
):
    service = DepartmentService(db)
    try:
        return await service.update_department(id, schema)
    except ValueError as e:
        # Check if the error is a missing record or validation failure
        status_code = (
            status.HTTP_404_NOT_FOUND
            if "not found" in str(e).lower()
            else status.HTTP_400_BAD_REQUEST
        )
        raise HTTPException(status_code=status_code, detail=str(e))


@router.delete(
    "/{id}",
    response_model=DepartmentResponse,
    summary="Delete a department",
    description="Soft-delete a department record. Admin role is required."
)
async def delete_department(
    id: UUID,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin)
):
    service = DepartmentService(db)
    try:
        return await service.delete_department(id)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )

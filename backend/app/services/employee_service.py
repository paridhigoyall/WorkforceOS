from datetime import datetime, timezone
from typing import List, Optional, Tuple
from uuid import UUID
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.employee import Employee
from app.models.user import User
from app.models.department import Department
from app.models.audit_log import AuditLog
from app.repositories.employee_repository import EmployeeRepository
from app.repositories.department_repository import DepartmentRepository
from app.schemas.employee import EmployeeCreate, EmployeeUpdate


class EmployeeService:
    def __init__(self, db_session: AsyncSession) -> None:
        self.db_session = db_session
        self.repo = EmployeeRepository(db_session)
        self.dept_repo = DepartmentRepository(db_session)

    async def onboard_employee(self, schema: EmployeeCreate, operator_id: UUID) -> Employee:
        """
        Onboards a new employee.
        Workflow:
        1. Validates that the base User exists.
        2. Validates that the User does not already have an Employee profile (1-to-1 mapping).
        3. Validates the target Department exists (if specified).
        4. Creates the Employee record.
        5. Logs the onboarding action in the AuditLog.
        """
        async with self.db_session.begin():
            # 1. Validate User existence
            user_stmt = select(User).where(User.id == schema.user_id)
            user_result = await self.db_session.execute(user_stmt)
            user = user_result.scalar_one_or_none()
            if not user:
                raise ValueError(f"Cannot onboard: User with ID {schema.user_id} does not exist.")

            # 2. Check for duplicate employee profile (1-to-1 constraint check)
            existing_emp = await self.repo.get_by_user_id(schema.user_id, include_deleted=True)
            if existing_emp:
                if existing_emp.is_deleted:
                    raise ValueError(
                        f"User {schema.user_id} already has a soft-deleted employee profile. "
                        "Please restore the profile instead of onboarding a new one."
                    )
                raise ValueError(f"User {schema.user_id} is already onboarded as an active employee.")

            # 3. Validate Department existence (if provided)
            if schema.department_id:
                dept = await self.dept_repo.get_by_id(schema.department_id)
                if not dept:
                    raise ValueError(f"Cannot onboard: Department with ID {schema.department_id} does not exist.")

            # 4. Create Employee
            db_emp = await self.repo.create(schema)

            # 5. Write to AuditLog
            audit_log = AuditLog(
                user_id=operator_id,  # Admin/operator executing the action
                action="ONBOARD_EMPLOYEE",
                target_type="employees",
                target_id=db_emp.id,
                details={
                    "user_id": str(schema.user_id),
                    "department_id": str(schema.department_id) if schema.department_id else None,
                    "hire_date": str(schema.hire_date)
                }
            )
            self.db_session.add(audit_log)

        return db_emp

    async def get_employee(self, id: UUID) -> Employee:
        """Fetch employee by ID, raising error if missing."""
        db_emp = await self.repo.get_by_id(id)
        if not db_emp:
            raise ValueError(f"Employee with ID {id} not found.")
        return db_emp

    async def list_employees(
        self,
        department_id: Optional[UUID] = None,
        limit: int = 100,
        offset: int = 0
    ) -> Tuple[List[Employee], int]:
        """Fetch paginated employees list with department filtering."""
        return await self.repo.list_paginated(
            department_id=department_id,
            limit=limit,
            offset=offset
        )

    async def update_employee(self, id: UUID, schema: EmployeeUpdate, operator_id: UUID) -> Employee:
        """
        Update employee details and log audit trail.
        """
        db_emp = await self.get_employee(id)

        async with self.db_session.begin():
            # If changing department, validate existence
            if schema.department_id and schema.department_id != db_emp.department_id:
                dept = await self.dept_repo.get_by_id(schema.department_id)
                if not dept:
                    raise ValueError(f"Department with ID {schema.department_id} does not exist.")

            # Extract fields that are changing for auditing
            update_data = schema.model_dump(exclude_unset=True)
            changes = {}
            for key, val in update_data.items():
                old_val = getattr(db_emp, key)
                if old_val != val:
                    changes[key] = {"old": str(old_val), "new": str(val)}

            # Perform update
            db_emp = await self.repo.update(db_emp, schema)

            # Audit log details
            if changes:
                audit_log = AuditLog(
                    user_id=operator_id,
                    action="UPDATE_EMPLOYEE",
                    target_type="employees",
                    target_id=db_emp.id,
                    details={"changes": changes}
                )
                self.db_session.add(audit_log)

        return db_emp

    async def offboard_employee(self, id: UUID, operator_id: UUID) -> Employee:
        """
        Soft delete the employee record and log action.
        """
        db_emp = await self.get_employee(id)

        async with self.db_session.begin():
            db_emp = await self.repo.delete(db_emp)
            
            audit_log = AuditLog(
                user_id=operator_id,
                action="OFFBOARD_EMPLOYEE",
                target_type="employees",
                target_id=db_emp.id,
                details={"offboard_date": str(datetime.now(timezone.utc))}
            )
            self.db_session.add(audit_log)

        return db_emp


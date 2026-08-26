"""
Leave service layer.

Follows workforce management conventions:
  - Takes an AsyncSession via __init__ and instantiates repositories
  - Encapsulates database transactions inside 'async with self.db_session.begin():' blocks
  - Raises ValueError on validation / business logic failures
  - Writes audit logs for every write operation (apply, approve, reject, cancel)
  - Prevents overlapping leave requests
  - Prevents approval of already-processed (non-PENDING) requests
  - Updates LeaveBalance used_days on approve / cancel
"""
from __future__ import annotations

from datetime import date, datetime, timezone
from typing import List, Optional, Tuple
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.audit_log import AuditLog
from app.models.employee import Employee
from app.models.leave import LeaveBalance, LeaveRequest, LeaveStatus, LeaveType
from app.repositories.leave_repository import LeaveBalanceRepository, LeaveRequestRepository
from app.schemas.leave import LeaveBalanceCreate, LeaveBalanceUpdate, LeaveRequestCreate


class LeaveService:
    """Service layer coordinating business rules for Leave requests and balances."""

    def __init__(self, db_session: AsyncSession) -> None:
        self.db_session = db_session
        self.leave_repo = LeaveRequestRepository(db_session)
        self.balance_repo = LeaveBalanceRepository(db_session)

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    async def _require_employee(self, employee_id: UUID) -> Employee:
        """
        Validate that the given employee_id belongs to an active (non-soft-deleted) employee.
        Raises ValueError if not found.
        """
        stmt = select(Employee).where(
            Employee.id == employee_id,
            Employee.is_deleted == False,  # noqa: E712
        )
        result = await self.db_session.execute(stmt)
        employee = result.scalar_one_or_none()
        if not employee:
            raise ValueError(f"Employee with ID {employee_id} does not exist or has been removed.")
        return employee

    def _calc_total_days(self, start_date, end_date) -> int:
        """Calculate inclusive calendar days between start_date and end_date."""
        return (end_date - start_date).days + 1

    # ------------------------------------------------------------------
    # Apply for leave
    # ------------------------------------------------------------------

    async def apply(self, schema: LeaveRequestCreate, requesting_user_id: UUID) -> LeaveRequest:
        """
        Submit a new leave request.

        Rules:
          - Employee must exist and not be soft-deleted.
          - end_date must be >= start_date (validated by schema, re-confirmed here).
          - No overlapping non-cancelled leave requests allowed for the employee.
          - Audit log: LEAVE_APPLY
        """
        async with self.db_session.begin():
            # Resolve employee_id: provided (Admin/HR path) or None (staff self-service)
            employee_id = schema.employee_id  # type: ignore[assignment]
            if employee_id is None:
                raise ValueError("employee_id must be resolved before calling apply().")

            employee = await self._require_employee(employee_id)

            # Business guard: date order
            if schema.end_date < schema.start_date:
                raise ValueError("end_date must be on or after start_date.")

            # Business guard: no overlapping requests
            overlap = await self.leave_repo.has_overlap(
                employee_id, schema.start_date, schema.end_date
            )
            if overlap:
                raise ValueError(
                    f"Employee {employee_id} already has a leave request overlapping "
                    f"{schema.start_date} – {schema.end_date}. "
                    "Cancel or reject the existing request first."
                )

            total_days = self._calc_total_days(schema.start_date, schema.end_date)

            db_leave = await self.leave_repo.create(
                employee_id=employee_id,
                leave_type=schema.leave_type,
                start_date=schema.start_date,
                end_date=schema.end_date,
                total_days=total_days,
                reason=schema.reason,
            )

            # Audit log
            audit = AuditLog(
                user_id=requesting_user_id,
                action="LEAVE_APPLY",
                target_type="leave_requests",
                target_id=db_leave.id,
                details={
                    "employee_id": str(employee_id),
                    "leave_type": schema.leave_type.value,
                    "start_date": str(schema.start_date),
                    "end_date": str(schema.end_date),
                    "total_days": total_days,
                    "reason": schema.reason,
                },
            )
            self.db_session.add(audit)

        return db_leave

    # ------------------------------------------------------------------
    # Approve
    # ------------------------------------------------------------------

    async def approve(self, leave_id: UUID, approver_user_id: UUID) -> LeaveRequest:
        """
        Approve a pending leave request.

        Rules:
          - The leave request must exist.
          - Status must be PENDING (prevent double-processing).
          - Updates LeaveBalance.used_days for the relevant year.
          - Audit log: LEAVE_APPROVE
        """
        async with self.db_session.begin():
            db_leave = await self.leave_repo.get_by_id(leave_id)
            if not db_leave:
                raise ValueError(f"Leave request with ID {leave_id} not found.")

            # Guard: prevent processing already-processed requests
            if db_leave.status != LeaveStatus.PENDING:
                raise ValueError(
                    f"Leave request {leave_id} cannot be approved — "
                    f"current status is '{db_leave.status.value}'. "
                    "Only PENDING requests can be approved."
                )

            now = datetime.now(timezone.utc)

            from app.schemas.leave import LeaveRequestUpdate
            db_leave = await self.leave_repo.update(
                db_leave,
                LeaveRequestUpdate(
                    status=LeaveStatus.APPROVED,
                    approved_by=approver_user_id,
                    approved_at=now,
                ),
            )

            # Deduct from leave balance for the year the leave starts in
            year = db_leave.start_date.year
            await self.balance_repo.increment_used(
                db_leave.employee_id, db_leave.leave_type, year, db_leave.total_days
            )

            # Audit log
            audit = AuditLog(
                user_id=approver_user_id,
                action="LEAVE_APPROVE",
                target_type="leave_requests",
                target_id=db_leave.id,
                details={
                    "employee_id": str(db_leave.employee_id),
                    "leave_type": db_leave.leave_type.value,
                    "start_date": str(db_leave.start_date),
                    "end_date": str(db_leave.end_date),
                    "total_days": db_leave.total_days,
                    "approved_at": now.isoformat(),
                },
            )
            self.db_session.add(audit)

            # Create in-app notification for employee
            emp = await self._require_employee(db_leave.employee_id)
            if emp.user_id:
                from app.models.notification import Notification, NotificationType
                notif = Notification(
                    user_id=emp.user_id,
                    title="Leave Request Approved",
                    message=f"Your {db_leave.leave_type.value} leave request for {db_leave.start_date} to {db_leave.end_date} ({db_leave.total_days} days) has been approved.",
                    type=NotificationType.LEAVE,
                    link="/leave",
                )
                self.db_session.add(notif)

        return db_leave

    # ------------------------------------------------------------------
    # Reject
    # ------------------------------------------------------------------

    async def reject(self, leave_id: UUID, approver_user_id: UUID) -> LeaveRequest:
        """
        Reject a pending leave request.

        Rules:
          - The leave request must exist.
          - Status must be PENDING (prevent double-processing).
          - Audit log: LEAVE_REJECT
        """
        async with self.db_session.begin():
            db_leave = await self.leave_repo.get_by_id(leave_id)
            if not db_leave:
                raise ValueError(f"Leave request with ID {leave_id} not found.")

            # Guard: prevent processing already-processed requests
            if db_leave.status != LeaveStatus.PENDING:
                raise ValueError(
                    f"Leave request {leave_id} cannot be rejected — "
                    f"current status is '{db_leave.status.value}'. "
                    "Only PENDING requests can be rejected."
                )

            now = datetime.now(timezone.utc)

            from app.schemas.leave import LeaveRequestUpdate
            db_leave = await self.leave_repo.update(
                db_leave,
                LeaveRequestUpdate(
                    status=LeaveStatus.REJECTED,
                    approved_by=approver_user_id,
                    approved_at=now,
                ),
            )

            # Audit log
            audit = AuditLog(
                user_id=approver_user_id,
                action="LEAVE_REJECT",
                target_type="leave_requests",
                target_id=db_leave.id,
                details={
                    "employee_id": str(db_leave.employee_id),
                    "leave_type": db_leave.leave_type.value,
                    "start_date": str(db_leave.start_date),
                    "end_date": str(db_leave.end_date),
                    "total_days": db_leave.total_days,
                    "rejected_at": now.isoformat(),
                },
            )
            self.db_session.add(audit)

            # Create in-app notification for employee
            emp = await self._require_employee(db_leave.employee_id)
            if emp.user_id:
                from app.models.notification import Notification, NotificationType
                notif = Notification(
                    user_id=emp.user_id,
                    title="Leave Request Rejected",
                    message=f"Your {db_leave.leave_type.value} leave request for {db_leave.start_date} to {db_leave.end_date} has been rejected.",
                    type=NotificationType.LEAVE,
                    link="/leave",
                )
                self.db_session.add(notif)

        return db_leave

    # ------------------------------------------------------------------
    # Cancel
    # ------------------------------------------------------------------

    async def cancel(self, leave_id: UUID, requesting_user_id: UUID) -> LeaveRequest:
        """
        Cancel a leave request (employee self-cancel or Admin/HR override).

        Rules:
          - The leave request must exist.
          - CANCELLED or REJECTED requests cannot be cancelled again.
          - If the request was previously APPROVED, used_days are refunded.
          - Audit log: LEAVE_CANCEL
        """
        async with self.db_session.begin():
            db_leave = await self.leave_repo.get_by_id(leave_id)
            if not db_leave:
                raise ValueError(f"Leave request with ID {leave_id} not found.")

            # Guard: already terminal states
            if db_leave.status in (LeaveStatus.CANCELLED, LeaveStatus.REJECTED):
                raise ValueError(
                    f"Leave request {leave_id} is already '{db_leave.status.value}' "
                    "and cannot be cancelled."
                )

            was_approved = db_leave.status == LeaveStatus.APPROVED

            from app.schemas.leave import LeaveRequestUpdate
            db_leave = await self.leave_repo.update(
                db_leave,
                LeaveRequestUpdate(status=LeaveStatus.CANCELLED),
            )

            # Refund balance if the request had been approved
            if was_approved:
                year = db_leave.start_date.year
                await self.balance_repo.decrement_used(
                    db_leave.employee_id, db_leave.leave_type, year, db_leave.total_days
                )

            # Audit log
            audit = AuditLog(
                user_id=requesting_user_id,
                action="LEAVE_CANCEL",
                target_type="leave_requests",
                target_id=db_leave.id,
                details={
                    "employee_id": str(db_leave.employee_id),
                    "leave_type": db_leave.leave_type.value,
                    "start_date": str(db_leave.start_date),
                    "end_date": str(db_leave.end_date),
                    "total_days": db_leave.total_days,
                    "was_approved": was_approved,
                    "cancelled_at": datetime.now(timezone.utc).isoformat(),
                },
            )
            self.db_session.add(audit)

        return db_leave

    # ------------------------------------------------------------------
    # Read operations
    # ------------------------------------------------------------------

    async def get_leave(self, leave_id: UUID) -> LeaveRequest:
        """Fetch leave request by ID, raising ValueError if not found."""
        db_leave = await self.leave_repo.get_by_id(leave_id)
        if not db_leave:
            raise ValueError(f"Leave request with ID {leave_id} not found.")
        return db_leave

    async def list_leaves(
        self,
        employee_id: Optional[UUID] = None,
        status: Optional[LeaveStatus] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> Tuple[List[LeaveRequest], int]:
        """Fetch paginated leave requests, optionally filtered by employee and/or status."""
        return await self.leave_repo.list_paginated(
            employee_id=employee_id,
            status=status,
            limit=limit,
            offset=offset,
        )

    # ------------------------------------------------------------------
    # Balance operations
    # ------------------------------------------------------------------

    async def allocate_balance(
        self, schema: LeaveBalanceCreate, requesting_user_id: UUID
    ) -> LeaveBalance:
        """
        Allocate (or overwrite) leave balance for an employee.
        Admin/HR only — enforced at the route layer.
        """
        async with self.db_session.begin():
            # Validate employee
            await self._require_employee(schema.employee_id)

            balance = await self.balance_repo.create(schema)

            # Audit log
            audit = AuditLog(
                user_id=requesting_user_id,
                action="LEAVE_BALANCE_ALLOCATE",
                target_type="leave_balances",
                target_id=balance.id,
                details={
                    "employee_id": str(schema.employee_id),
                    "leave_type": schema.leave_type.value,
                    "year": schema.year,
                    "allocated_days": schema.allocated_days,
                },
            )
            self.db_session.add(audit)

        return balance

    async def update_balance(
        self, balance_id: UUID, schema: LeaveBalanceUpdate, requesting_user_id: UUID
    ) -> LeaveBalance:
        """Adjust allocated_days on an existing balance entry. Admin/HR only."""
        async with self.db_session.begin():
            balance = await self.balance_repo.get_by_id(balance_id)
            if not balance:
                raise ValueError(f"Leave balance with ID {balance_id} not found.")

            old_allocated = balance.allocated_days
            balance = await self.balance_repo.update(balance, schema)

            # Audit log
            audit = AuditLog(
                user_id=requesting_user_id,
                action="LEAVE_BALANCE_UPDATE",
                target_type="leave_balances",
                target_id=balance.id,
                details={
                    "employee_id": str(balance.employee_id),
                    "leave_type": balance.leave_type.value,
                    "year": balance.year,
                    "old_allocated_days": old_allocated,
                    "new_allocated_days": schema.allocated_days,
                },
            )
            self.db_session.add(audit)

        return balance

    async def list_balances(
        self, employee_id: UUID, year: Optional[int] = None
    ) -> List[LeaveBalance]:
        """Fetch all balance entries for an employee, optionally filtered by year."""
        return await self.balance_repo.list_for_employee(employee_id, year)

    async def run_accrual_engine(self, employee_id: UUID, year: int, requesting_user_id: UUID) -> List[LeaveBalance]:
        """
        Dynamically calculate and accrue leave balances for an employee for a specific year.
        Formula:
          - 1.5 days accrued per completed month of service in that year.
          - If hired in previous year, start accrual from Jan.
          - If hired in target year, start from hire month.
        """
        async with self.db_session.begin():
            employee = await self._require_employee(employee_id)
            hire_date = employee.hire_date
            
            # Determine start month of accrual in the target year
            if hire_date.year < year:
                start_month = 1
            elif hire_date.year == year:
                start_month = hire_date.month
            else:
                start_month = 13
            
            # End month is either current month (if current year matches target year) or 12
            current_date = date.today()
            if current_date.year == year:
                end_month = min(12, current_date.month)
            elif current_date.year > year:
                end_month = 12
            else:
                end_month = 0
            
            months_served = max(0, end_month - start_month + 1)
            accrued_days = months_served * 1.5
            
            from app.models.leave import LeaveType, LeaveBalance
            from app.schemas.leave import LeaveBalanceCreate, LeaveBalanceUpdate
            
            updated_balances = []
            for leave_type in (LeaveType.CASUAL, LeaveType.SICK):
                stmt = select(LeaveBalance).where(
                    LeaveBalance.employee_id == employee_id,
                    LeaveBalance.leave_type == leave_type,
                    LeaveBalance.year == year
                )
                res = await self.db_session.execute(stmt)
                balance = res.scalar_one_or_none()
                
                if balance:
                    balance = await self.balance_repo.update(
                        balance,
                        LeaveBalanceUpdate(allocated_days=int(accrued_days))
                    )
                else:
                    balance = await self.balance_repo.create(
                        LeaveBalanceCreate(
                            employee_id=employee_id,
                            leave_type=leave_type,
                            year=year,
                            allocated_days=int(accrued_days)
                        )
                    )
                updated_balances.append(balance)
                
                audit = AuditLog(
                    user_id=requesting_user_id,
                    action="LEAVE_ACCRUAL",
                    target_type="leave_balances",
                    target_id=balance.id,
                    details={
                        "employee_id": str(employee_id),
                        "leave_type": leave_type.value,
                        "year": year,
                        "months_served": months_served,
                        "accrued_days": accrued_days,
                    },
                )
                self.db_session.add(audit)
                
            return updated_balances

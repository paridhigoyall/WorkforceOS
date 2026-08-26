from __future__ import annotations

import pytest
from datetime import date
from uuid import uuid4
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.models.employee import Employee
from app.models.leave import LeaveType, LeaveStatus, LeaveBalance
from app.schemas.leave import LeaveRequestCreate, LeaveBalanceCreate
from app.services.leave_service import LeaveService


class TestLeaveService:
    async def test_apply_leave_success(
        self,
        db_session: AsyncSession,
        test_employee: Employee,
        staff_user: User,
    ):
        service = LeaveService(db_session)
        # Allocate balance first (method is allocate_balance, param is requesting_user_id)
        await service.allocate_balance(
            LeaveBalanceCreate(
                employee_id=test_employee.id,
                leave_type=LeaveType.CASUAL,
                year=2025,
                allocated_days=10,
            ),
            requesting_user_id=staff_user.id,
        )

        schema = LeaveRequestCreate(
            employee_id=test_employee.id,
            leave_type=LeaveType.CASUAL,
            start_date=date(2025, 4, 1),
            end_date=date(2025, 4, 5),
            reason="Family vacation",
        )
        req = await service.apply(schema, requesting_user_id=staff_user.id)

        assert req.id is not None
        assert req.status == LeaveStatus.PENDING
        assert req.total_days == 5

    async def test_invalid_date_range_fails(
        self,
        db_session: AsyncSession,
        test_employee: Employee,
        staff_user: User,
    ):
        service = LeaveService(db_session)
        with pytest.raises(Exception):  # Pydantic or ValueError validator
            schema = LeaveRequestCreate(
                employee_id=test_employee.id,
                leave_type=LeaveType.SICK,
                start_date=date(2025, 4, 10),
                end_date=date(2025, 4, 5),  # End before start
                reason="Invalid dates",
            )
            await service.apply(schema, requesting_user_id=staff_user.id)

    async def test_overlapping_leave_fails(
        self,
        db_session: AsyncSession,
        test_employee: Employee,
        staff_user: User,
    ):
        service = LeaveService(db_session)
        # Create initial leave
        await service.apply(
            LeaveRequestCreate(
                employee_id=test_employee.id,
                leave_type=LeaveType.UNPAID,
                start_date=date(2025, 5, 1),
                end_date=date(2025, 5, 10),
                reason="Initial leave",
            ),
            requesting_user_id=staff_user.id,
        )

        # Overlapping request
        with pytest.raises(ValueError, match="already has a leave request overlapping"):
            await service.apply(
                LeaveRequestCreate(
                    employee_id=test_employee.id,
                    leave_type=LeaveType.UNPAID,
                    start_date=date(2025, 5, 5),
                    end_date=date(2025, 5, 15),
                    reason="Overlapping leave",
                ),
                requesting_user_id=staff_user.id,
            )

    async def test_approve_and_reapprove_leave(
        self,
        db_session: AsyncSession,
        test_employee: Employee,
        staff_user: User,
        admin_user: User,
    ):
        service = LeaveService(db_session)
        req = await service.apply(
            LeaveRequestCreate(
                employee_id=test_employee.id,
                leave_type=LeaveType.UNPAID,
                start_date=date(2025, 6, 1),
                end_date=date(2025, 6, 3),
                reason="Short break",
            ),
            requesting_user_id=staff_user.id,
        )

        approved = await service.approve(req.id, approver_user_id=admin_user.id)
        assert approved.status == LeaveStatus.APPROVED
        assert approved.approved_by == admin_user.id

        # Re-approval must fail
        with pytest.raises(ValueError, match="cannot be approved"):
            await service.approve(req.id, approver_user_id=admin_user.id)

    async def test_reject_and_cancel_leave(
        self,
        db_session: AsyncSession,
        test_employee: Employee,
        staff_user: User,
        admin_user: User,
    ):
        service = LeaveService(db_session)
        req = await service.apply(
            LeaveRequestCreate(
                employee_id=test_employee.id,
                leave_type=LeaveType.UNPAID,
                start_date=date(2025, 7, 1),
                end_date=date(2025, 7, 2),
                reason="Request",
            ),
            requesting_user_id=staff_user.id,
        )

        rejected = await service.reject(req.id, approver_user_id=admin_user.id)
        assert rejected.status == LeaveStatus.REJECTED

        # Cannot cancel a rejected leave
        with pytest.raises(ValueError, match="cannot be cancelled"):
            await service.cancel(req.id, requesting_user_id=staff_user.id)

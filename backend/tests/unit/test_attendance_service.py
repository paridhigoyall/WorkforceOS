from __future__ import annotations

import pytest
from datetime import date, datetime, timezone
from uuid import uuid4
from decimal import Decimal
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.employee import Employee
from app.models.attendance import AttendanceStatus
from app.services.attendance_service import AttendanceService


class TestAttendanceService:
    async def test_check_in_on_time(
        self,
        db_session: AsyncSession,
        test_employee: Employee,
    ):
        service = AttendanceService(db_session)
        check_in_time = datetime(2025, 3, 1, 8, 45, 0, tzinfo=timezone.utc)
        record = await service.check_in(test_employee.id, check_in_time=check_in_time)

        assert record.id is not None
        assert record.attendance_status == AttendanceStatus.PRESENT
        assert record.check_out_time is None

    async def test_check_in_late(
        self,
        db_session: AsyncSession,
        test_employee: Employee,
    ):
        service = AttendanceService(db_session)
        check_in_time = datetime(2025, 3, 2, 9, 30, 0, tzinfo=timezone.utc)
        record = await service.check_in(test_employee.id, check_in_time=check_in_time)

        assert record.attendance_status == AttendanceStatus.LATE

    async def test_duplicate_check_in_fails(
        self,
        db_session: AsyncSession,
        test_employee: Employee,
    ):
        service = AttendanceService(db_session)
        check_in_time = datetime(2025, 3, 3, 8, 30, 0, tzinfo=timezone.utc)
        await service.check_in(test_employee.id, check_in_time=check_in_time)

        with pytest.raises(ValueError, match="already checked in"):
            await service.check_in(test_employee.id, check_in_time=check_in_time)

    async def test_check_out_calculates_overtime(
        self,
        db_session: AsyncSession,
        test_employee: Employee,
    ):
        service = AttendanceService(db_session)
        check_in_time = datetime(2025, 3, 4, 8, 0, 0, tzinfo=timezone.utc)
        record = await service.check_in(test_employee.id, check_in_time=check_in_time)

        check_out_time = datetime(2025, 3, 4, 18, 0, 0, tzinfo=timezone.utc)
        completed = await service.check_out(record.id, check_out_time=check_out_time)

        assert completed.total_hours == Decimal("10.00")
        assert completed.check_out_time is not None

    async def test_check_out_half_day(
        self,
        db_session: AsyncSession,
        test_employee: Employee,
    ):
        service = AttendanceService(db_session)
        record = await service.check_in(
            test_employee.id,
            check_in_time=datetime(2025, 3, 5, 9, 0, 0, tzinfo=timezone.utc),
        )
        completed = await service.check_out(
            record.id,
            check_out_time=datetime(2025, 3, 5, 12, 0, 0, tzinfo=timezone.utc),
        )
        assert completed.attendance_status == AttendanceStatus.HALF_DAY
        assert completed.total_hours == Decimal("3.00")

    async def test_double_check_out_fails(
        self,
        db_session: AsyncSession,
        test_employee: Employee,
    ):
        service = AttendanceService(db_session)
        record = await service.check_in(
            test_employee.id,
            check_in_time=datetime(2025, 3, 6, 8, 30, 0, tzinfo=timezone.utc),
        )
        await service.check_out(
            record.id,
            check_out_time=datetime(2025, 3, 6, 17, 30, 0, tzinfo=timezone.utc),
        )
        with pytest.raises(ValueError, match="already checked out"):
            await service.check_out(
                record.id,
                check_out_time=datetime(2025, 3, 6, 18, 0, 0, tzinfo=timezone.utc),
            )

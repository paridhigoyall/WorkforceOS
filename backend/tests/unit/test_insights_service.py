from __future__ import annotations

import pytest
from datetime import date, datetime, timezone
from uuid import uuid4
from decimal import Decimal
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.employee import Employee
from app.models.department import Department
from app.models.attendance import Attendance, AttendanceStatus
from app.services.insights_service import InsightsService


class TestInsightsService:
    async def test_insights_calculations(
        self,
        db_session: AsyncSession,
        test_employee: Employee,
        test_department: Department,
    ):
        service = InsightsService(db_session)

        # Add attendance records
        att1 = Attendance(
            employee_id=test_employee.id,
            attendance_date=date(2025, 1, 10),
            check_in_time=datetime(2025, 1, 10, 8, 30, 0, tzinfo=timezone.utc),
            check_out_time=datetime(2025, 1, 10, 17, 30, 0, tzinfo=timezone.utc),
            total_hours=Decimal("9.00"),
            attendance_status=AttendanceStatus.PRESENT,
        )
        att2 = Attendance(
            employee_id=test_employee.id,
            attendance_date=date(2025, 1, 11),
            check_in_time=datetime(2025, 1, 11, 9, 30, 0, tzinfo=timezone.utc),
            check_out_time=datetime(2025, 1, 11, 17, 30, 0, tzinfo=timezone.utc),
            total_hours=Decimal("8.00"),
            attendance_status=AttendanceStatus.LATE,
        )
        db_session.add_all([att1, att2])
        await db_session.flush()

        # 1. Attendance Insights
        att_insights = await service.get_attendance_insights(test_employee.id)
        assert att_insights.total_records >= 2
        assert att_insights.average_attendance_rate == 100.0
        assert att_insights.late_check_ins >= 1

        # 2. Department Insights
        dept_insights = await service.get_department_insights()
        assert len(dept_insights) >= 1
        target_dept = next((d for d in dept_insights if d.department_id == test_department.id), None)
        assert target_dept is not None
        assert target_dept.headcount >= 1

        # 3. Turnover Risk Overview
        turnover = await service.get_turnover_risk_overview()
        assert turnover.total_evaluated >= 1
        assert turnover.average_workforce_risk_score >= 0

        # 4. AI Prediction Dataset
        dataset = await service.get_ai_prediction_dataset()
        assert len(dataset.data) >= 1

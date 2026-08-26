from __future__ import annotations

import pytest
from datetime import date, datetime, timezone
from uuid import uuid4
from httpx import AsyncClient

from app.models.employee import Employee


class TestAttendanceAPI:
    async def test_check_in_api(
        self,
        client: AsyncClient,
        admin_headers: dict[str, str],
        test_employee: Employee,
    ):
        """Admin can record check-in by specifying employee_id."""
        res = await client.post(
            "/api/attendance/check-in",
            headers=admin_headers,
            json={
                "employee_id": str(test_employee.id),
                "attendance_date": "2025-08-01",
                "check_in_time": "2025-08-01T08:30:00Z",
            },
        )
        assert res.status_code == 201
        data = res.json()
        assert data["attendance_status"] == "PRESENT"
        assert data["employee_id"] == str(test_employee.id)

    async def test_check_out_api(
        self,
        client: AsyncClient,
        admin_headers: dict[str, str],
        test_employee: Employee,
    ):
        """Admin can record check-in then check-out, total_hours should be 9.0."""
        # 1. Check in
        in_res = await client.post(
            "/api/attendance/check-in",
            headers=admin_headers,
            json={
                "employee_id": str(test_employee.id),
                "attendance_date": "2025-08-02",
                "check_in_time": "2025-08-02T08:00:00Z",
            },
        )
        assert in_res.status_code == 201
        att_id = in_res.json()["id"]

        # 2. Check out
        out_res = await client.post(
            f"/api/attendance/{att_id}/check-out",
            headers=admin_headers,
            json={
                "check_out_time": "2025-08-02T17:00:00Z",
            },
        )
        assert out_res.status_code == 200
        data = out_res.json()
        assert float(data["total_hours"]) == 9.0

    async def test_list_attendance(
        self,
        client: AsyncClient,
        admin_headers: dict[str, str],
        test_employee: Employee,
    ):
        """Admin can list all attendance records filtered by employee_id."""
        res = await client.get(
            "/api/attendance/",
            headers=admin_headers,
            params={"employee_id": str(test_employee.id)},
        )
        assert res.status_code == 200
        assert isinstance(res.json(), list)

    async def test_staff_cannot_checkin_for_others(
        self,
        client: AsyncClient,
        staff_headers: dict[str, str],
        test_employee: Employee,
    ):
        """Staff users cannot record check-in for other employees."""
        # Create a different employee UUID (not belonging to the staff user)
        other_emp_id = uuid4()
        res = await client.post(
            "/api/attendance/check-in",
            headers=staff_headers,
            json={
                "employee_id": str(other_emp_id),
                "check_in_time": "2025-08-03T09:00:00Z",
            },
        )
        assert res.status_code == 403

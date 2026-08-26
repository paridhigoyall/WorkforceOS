from __future__ import annotations

import pytest
from httpx import AsyncClient

from app.models.employee import Employee


class TestLeaveAPI:
    async def test_apply_and_approve_leave(
        self,
        client: AsyncClient,
        staff_headers: dict[str, str],
        admin_headers: dict[str, str],
        test_employee: Employee,
    ):
        # 1. Apply for leave
        apply_res = await client.post(
            "/api/leave/",
            headers=staff_headers,
            json={
                "employee_id": str(test_employee.id),
                "leave_type": "UNPAID",
                "start_date": "2025-09-01",
                "end_date": "2025-09-05",
                "reason": "Personal time off",
            },
        )
        assert apply_res.status_code == 201
        leave_id = apply_res.json()["id"]

        # 2. Staff cannot approve leave (403 Forbidden)
        staff_appr = await client.post(f"/api/leave/{leave_id}/approve", headers=staff_headers)
        assert staff_appr.status_code == 403

        # 3. Admin can approve leave (200 OK)
        admin_appr = await client.post(f"/api/leave/{leave_id}/approve", headers=admin_headers)
        assert admin_appr.status_code == 200
        assert admin_appr.json()["status"] == "APPROVED"

    async def test_apply_and_reject_leave(
        self,
        client: AsyncClient,
        staff_headers: dict[str, str],
        admin_headers: dict[str, str],
        test_employee: Employee,
    ):
        apply_res = await client.post(
            "/api/leave/",
            headers=staff_headers,
            json={
                "employee_id": str(test_employee.id),
                "leave_type": "UNPAID",
                "start_date": "2025-09-10",
                "end_date": "2025-09-12",
                "reason": "Conference",
            },
        )
        assert apply_res.status_code == 201
        leave_id = apply_res.json()["id"]

        reject_res = await client.post(f"/api/leave/{leave_id}/reject", headers=admin_headers)
        assert reject_res.status_code == 200
        assert reject_res.json()["status"] == "REJECTED"

    async def test_cancel_leave(
        self,
        client: AsyncClient,
        staff_headers: dict[str, str],
        test_employee: Employee,
    ):
        apply_res = await client.post(
            "/api/leave/",
            headers=staff_headers,
            json={
                "employee_id": str(test_employee.id),
                "leave_type": "UNPAID",
                "start_date": "2025-09-20",
                "end_date": "2025-09-21",
                "reason": "Change of plans",
            },
        )
        assert apply_res.status_code == 201
        leave_id = apply_res.json()["id"]

        cancel_res = await client.post(f"/api/leave/{leave_id}/cancel", headers=staff_headers)
        assert cancel_res.status_code == 200
        assert cancel_res.json()["status"] == "CANCELLED"

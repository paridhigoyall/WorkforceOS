from __future__ import annotations

import pytest
from httpx import AsyncClient

from app.models.employee import Employee


class TestPayrollAPI:
    async def test_generate_payroll_admin(
        self,
        client: AsyncClient,
        admin_headers: dict[str, str],
        test_employee: Employee,
    ):
        res = await client.post(
            "/api/payroll/generate",
            headers=admin_headers,
            json={"year": 2025, "month": 10},
        )
        assert res.status_code == 200
        data = res.json()
        assert data["year"] == 2025
        assert data["month"] == 10
        assert data["status"] == "DRAFT"
        assert len(data["records"]) >= 1

    async def test_generate_payroll_staff_forbidden(
        self,
        client: AsyncClient,
        staff_headers: dict[str, str],
    ):
        res = await client.post(
            "/api/payroll/generate",
            headers=staff_headers,
            json={"year": 2025, "month": 10},
        )
        assert res.status_code == 403

    async def test_approve_payroll_period(
        self,
        client: AsyncClient,
        admin_headers: dict[str, str],
        test_employee: Employee,
    ):
        # 1. Generate
        gen_res = await client.post(
            "/api/payroll/generate",
            headers=admin_headers,
            json={"year": 2025, "month": 11},
        )
        assert gen_res.status_code == 200
        period_id = gen_res.json()["id"]

        # 2. Approve
        appr_res = await client.post(
            f"/api/payroll/periods/{period_id}/approve",
            headers=admin_headers,
        )
        assert appr_res.status_code == 200
        assert appr_res.json()["status"] == "APPROVED"

        # 3. View payslip
        record_id = appr_res.json()["records"][0]["id"]
        slip_res = await client.get(
            f"/api/payroll/records/{record_id}/payslip",
            headers=admin_headers,
        )
        assert slip_res.status_code == 200
        assert slip_res.json()["net_pay"] > 0

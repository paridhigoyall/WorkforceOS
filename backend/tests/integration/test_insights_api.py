from __future__ import annotations

import pytest
from httpx import AsyncClient

from app.models.employee import Employee


class TestInsightsAPI:
    async def test_get_all_insights_endpoints(
        self,
        client: AsyncClient,
        admin_headers: dict[str, str],
        test_employee: Employee,
    ):
        # 1. Attendance insights
        att_res = await client.get("/api/insights/attendance", headers=admin_headers)
        assert att_res.status_code == 200

        # 2. Leave insights
        leave_res = await client.get("/api/insights/leave", headers=admin_headers)
        assert leave_res.status_code == 200

        # 3. Department insights
        dept_res = await client.get("/api/insights/departments", headers=admin_headers)
        assert dept_res.status_code == 200

        # 4. AI dataset
        dataset_res = await client.get("/api/insights/ai-prediction-dataset", headers=admin_headers)
        assert dataset_res.status_code == 200
        assert "data" in dataset_res.json()

        # 5. Turnover overview
        to_res = await client.get("/api/insights/turnover-risk/overview", headers=admin_headers)
        assert to_res.status_code == 200
        assert "average_workforce_risk_score" in to_res.json()

        # 6. Employee-specific turnover risk
        emp_to_res = await client.get(
            f"/api/insights/turnover-risk/employee/{test_employee.id}",
            headers=admin_headers,
        )
        assert emp_to_res.status_code == 200
        assert "flight_risk_score" in emp_to_res.json()

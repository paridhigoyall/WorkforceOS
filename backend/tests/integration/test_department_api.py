from __future__ import annotations

import pytest
from uuid import uuid4
from httpx import AsyncClient

from app.models.department import Department


class TestDepartmentAPI:
    async def test_create_department_admin(
        self,
        client: AsyncClient,
        admin_headers: dict[str, str],
    ):
        name = f"Finance_{uuid4().hex[:6]}"
        res = await client.post(
            "/api/departments/",
            headers=admin_headers,
            json={
                "name": name,
                "description": "Financial Operations",
            },
        )
        assert res.status_code == 201
        data = res.json()
        assert data["name"] == name

    async def test_create_department_staff_forbidden(
        self,
        client: AsyncClient,
        staff_headers: dict[str, str],
    ):
        res = await client.post(
            "/api/departments/",
            headers=staff_headers,
            json={
                "name": "Unauthorized Dept",
            },
        )
        assert res.status_code == 403

    async def test_list_departments(
        self,
        client: AsyncClient,
        staff_headers: dict[str, str],
        test_department: Department,
    ):
        res = await client.get("/api/departments/", headers=staff_headers)
        assert res.status_code == 200
        data = res.json()
        assert isinstance(data, list)
        assert any(d["id"] == str(test_department.id) for d in data)

    async def test_update_department(
        self,
        client: AsyncClient,
        admin_headers: dict[str, str],
        test_department: Department,
    ):
        res = await client.put(
            f"/api/departments/{test_department.id}",
            headers=admin_headers,
            json={"description": "Updated Description"},
        )
        assert res.status_code == 200
        assert res.json()["description"] == "Updated Description"

    async def test_delete_department(
        self,
        client: AsyncClient,
        admin_headers: dict[str, str],
        test_department: Department,
    ):
        res = await client.delete(
            f"/api/departments/{test_department.id}",
            headers=admin_headers,
        )
        assert res.status_code == 200
        assert res.json()["is_deleted"] is True

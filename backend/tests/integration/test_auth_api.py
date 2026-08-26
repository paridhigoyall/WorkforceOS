from __future__ import annotations

import pytest
from uuid import uuid4
import pyotp
from httpx import AsyncClient

from app.models.user import User


class TestAuthAPI:
    async def test_register_api(self, client: AsyncClient):
        email = f"api_user_{uuid4().hex[:6]}@test.com"
        res = await client.post(
            "/api/auth/register",
            json={
                "email": email,
                "password": "StrongPassword123!",
                "role": "staff",
            },
        )
        assert res.status_code == 201
        data = res.json()
        assert data["user"]["email"] == email
        assert "access_token" in data
        assert "refresh_token" in data

    async def test_login_api_success(self, client: AsyncClient, staff_user: User):
        res = await client.post(
            "/api/auth/login",
            data={
                "username": staff_user.email,
                "password": "StaffPass123!",
            },
        )
        assert res.status_code == 200
        data = res.json()
        assert "access_token" in data
        assert data["mfa_required"] is False

    async def test_login_api_invalid_credentials(self, client: AsyncClient, staff_user: User):
        res = await client.post(
            "/api/auth/login",
            data={
                "username": staff_user.email,
                "password": "IncorrectPassword!",
            },
        )
        assert res.status_code == 401
        assert "detail" in res.json()

    async def test_get_me_unauthorized(self, client: AsyncClient):
        res = await client.get("/api/auth/me")
        assert res.status_code == 401

    async def test_get_me_authorized(self, client: AsyncClient, staff_headers: dict[str, str], staff_user: User):
        res = await client.get("/api/auth/me", headers=staff_headers)
        assert res.status_code == 200
        data = res.json()
        assert data["email"] == staff_user.email
        assert data["role"] == staff_user.role.value

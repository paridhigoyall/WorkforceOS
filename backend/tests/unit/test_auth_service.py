from __future__ import annotations

import pytest
from uuid import uuid4
import pyotp
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User, UserRole
from app.schemas.auth import UserRegister, UserLogin
from app.services.auth_service import AuthService
from app.core.security import decode_token


class TestAuthService:
    async def test_register_success(self, db_session: AsyncSession):
        service = AuthService(db_session)
        schema = UserRegister(
            email=f"new_user_{uuid4().hex[:6]}@example.com",
            password="StrongPassword123!",
            role=UserRole.STAFF,
        )
        user, access_token, refresh_token = await service.register(schema)

        assert user.id is not None
        assert user.email == schema.email
        assert user.role == UserRole.STAFF
        assert access_token is not None
        assert refresh_token is not None

        payload = decode_token(access_token)
        assert payload["sub"] == str(user.id)
        assert payload["type"] == "access"

    async def test_register_duplicate_email_fails(self, db_session: AsyncSession, staff_user: User):
        service = AuthService(db_session)
        schema = UserRegister(
            email=staff_user.email,
            password="AnotherPassword123!",
            role=UserRole.STAFF,
        )
        with pytest.raises(ValueError, match="already registered"):
            await service.register(schema)

    async def test_login_success_without_mfa(self, db_session: AsyncSession, staff_user: User):
        service = AuthService(db_session)
        payload = type("Payload", (), {"username": staff_user.email, "password": "StaffPass123!"})()
        res = await service.login(payload)

        assert res.mfa_token is None
        assert res.access_token is not None
        assert res.refresh_token is not None

    async def test_login_invalid_password_fails(self, db_session: AsyncSession, staff_user: User):
        service = AuthService(db_session)
        payload = type("Payload", (), {"username": staff_user.email, "password": "WrongPassword!"})()
        with pytest.raises(ValueError, match="Invalid email or password"):
            await service.login(payload)

    async def test_login_nonexistent_user_fails(self, db_session: AsyncSession):
        service = AuthService(db_session)
        payload = type("Payload", (), {"username": "nonexistent@example.com", "password": "AnyPassword!"})()
        with pytest.raises(ValueError, match="Invalid email or password"):
            await service.login(payload)

    async def test_mfa_lifecycle(self, db_session: AsyncSession, staff_user: User):
        service = AuthService(db_session)

        # 1. Setup MFA
        setup_res = await service.setup_mfa(staff_user.id)
        assert setup_res.secret is not None
        assert "otpauth://" in setup_res.otpauth_url

        totp = pyotp.TOTP(setup_res.secret)
        valid_code = totp.now()

        # 2. Enable MFA with invalid code should fail
        with pytest.raises(ValueError, match="Invalid TOTP code"):
            await service.enable_mfa(staff_user.id, "StaffPass123!", "000000")

        # 3. Enable MFA with valid code
        await service.enable_mfa(staff_user.id, "StaffPass123!", valid_code)
        await db_session.refresh(staff_user)
        assert staff_user.is_mfa_enabled is True

        # 4. Login now returns MFA challenge token
        payload = type("Payload", (), {"username": staff_user.email, "password": "StaffPass123!"})()
        login_res = await service.login(payload)
        assert login_res.mfa_token is not None

        # 5. Verify MFA challenge with invalid code should fail
        with pytest.raises(ValueError, match="Invalid 2FA code"):
            await service.verify_mfa_login(login_res.mfa_token, "999999")

        # 6. Verify MFA challenge with valid code succeeds
        verified_token = await service.verify_mfa_login(login_res.mfa_token, totp.now())
        assert verified_token.access_token is not None

        # 7. Disable MFA
        await service.disable_mfa(staff_user.id, "StaffPass123!", totp.now())
        await db_session.refresh(staff_user)
        assert staff_user.is_mfa_enabled is False

    async def test_rotate_refresh_token(self, db_session: AsyncSession, staff_user: User):
        service = AuthService(db_session)
        payload = type("Payload", (), {"username": staff_user.email, "password": "StaffPass123!"})()
        login_res = await service.login(payload)

        rotated = await service.rotate_refresh_token(login_res.refresh_token)
        assert rotated.access_token is not None
        assert rotated.refresh_token is not None

    async def test_rotate_invalid_refresh_token_fails(self, db_session: AsyncSession):
        service = AuthService(db_session)
        with pytest.raises(ValueError, match="Refresh token is invalid or has expired"):
            await service.rotate_refresh_token("invalid.token.payload")

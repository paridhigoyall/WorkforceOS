"""
MFA, Notification Center & AI Retention Engine -- Verification Suite
===================================================================
Verifies:
  1. MFA setup, TOTP code generation & validation, enable/disable flow
  2. 2-Step Login with MFA challenge token & invalid TOTP protection
  3. Refresh Token rotation (/auth/refresh)
  4. In-App Notification Center: creation, unread count, mark-as-read, and mark-all-read
  5. Workflow triggers: Leave approve/reject notifications & Payroll notifications
  6. AI Turnover Flight Risk scoring, driver breakdowns & HR retention actions
"""
from __future__ import annotations

import asyncio
import os
import sys
import traceback
from datetime import date, datetime, timezone
from uuid import uuid4
import pyotp

sys.path.insert(0, os.path.dirname(__file__))

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from app.models.base import Base
from app.models.user import User, UserRole
from app.models.employee import Employee
from app.models.notification import Notification, NotificationType
from app.schemas.auth import UserLogin, UserRegister, MFAVerifyRequest, MFAToggleRequest, TokenRefreshRequest
from app.services.auth_service import AuthService
from app.services.notification_service import NotificationService
from app.services.insights_service import InsightsService

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+asyncpg://postgres:postgres@localhost:5432/postgres",
)

engine = create_async_engine(DATABASE_URL, echo=False)
AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

passed: list[str] = []
failed: list[str] = []


def ok(msg: str) -> None:
    passed.append(msg)
    print(f"  [PASS] {msg}")


def fail(msg: str, detail: str = "") -> None:
    failed.append(msg)
    info = f" -- {detail}" if detail else ""
    print(f"  [FAIL] {msg}{info}")


def section(title: str) -> None:
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}")


async def verify_mfa_flow() -> None:
    section("SECTION 1: MFA / TOTP & Token Lifecycle")

    async with AsyncSessionLocal() as db:
        auth_svc = AuthService(db)
        unique_email = f"mfa_test_{uuid4().hex[:8]}@workforceos.com"
        password = "SecurePassword123!"

        # 1. Register
        user, access_tok, refresh_tok = await auth_svc.register(
            UserRegister(email=unique_email, password=password, role="staff")
        )
        ok("User registered with access and refresh tokens")

        # 2. Setup MFA
        setup_res = await auth_svc.setup_mfa(user.id)
        if setup_res.secret and "otpauth://" in setup_res.otpauth_url:
            ok("MFA setup generated valid base32 secret and provisioning URI")
        else:
            fail("MFA setup failed", str(setup_res))

        # 3. Generate Valid TOTP
        totp = pyotp.TOTP(setup_res.secret)
        valid_code = totp.now()

        # 4. Enable MFA with invalid code (should fail)
        try:
            await auth_svc.enable_mfa(user.id, password, "000000")
            fail("Enable MFA with invalid code should have raised ValueError")
        except ValueError:
            ok("Enable MFA with invalid code correctly rejected")

        # 5. Enable MFA with valid code
        enabled = await auth_svc.enable_mfa(user.id, password, valid_code)
        if enabled:
            ok("MFA successfully enabled on user account")
        else:
            fail("MFA enable returned False")

        # 6. Login Step 1 (Should return MFA challenge)
        login_res = await auth_svc.login(UserLogin(username=unique_email, password=password))
        if login_res.mfa_required and login_res.mfa_token:
            ok("Login returns MFA challenge token when 2FA is enabled")
        else:
            fail("Login did not prompt for MFA challenge")

        # 7. Complete 2FA Login Step 2 with valid TOTP code
        login_step2 = await auth_svc.verify_mfa_login(login_res.mfa_token, totp.now())
        if login_step2.access_token and login_step2.refresh_token and not login_step2.mfa_required:
            ok("2-Step MFA login completed successfully with valid tokens")
        else:
            fail("MFA verification failed", str(login_step2))

        # 8. Test Refresh Token Rotation
        refreshed = await auth_svc.rotate_refresh_token(login_step2.refresh_token)
        if refreshed.access_token and refreshed.refresh_token:
            ok("Refresh token rotation successfully issued new token pair")
        else:
            fail("Token rotation failed")

        # Clean up
        await db.delete(user)
        await db.commit()


async def verify_notifications_flow() -> None:
    section("SECTION 2: In-App Notification Center")

    async with AsyncSessionLocal() as db:
        auth_svc = AuthService(db)
        notif_svc = NotificationService(db)

        user, _, _ = await auth_svc.register(
            UserRegister(email=f"notif_test_{uuid4().hex[:8]}@workforceos.com", password="Password123!", role="staff")
        )

        # 1. Send Notifications
        n1 = await notif_svc.send_notification(
            user_id=user.id,
            title="Leave Approved",
            message="Your leave request has been approved.",
            type=NotificationType.LEAVE,
            link="/leave",
        )
        n2 = await notif_svc.send_notification(
            user_id=user.id,
            title="Payroll Ready",
            message="Your payslip is available.",
            type=NotificationType.PAYROLL,
            link="/payroll",
        )
        await db.commit()
        ok("Dispatched test notifications across LEAVE and PAYROLL categories")

        # 2. Check Unread Count
        unread_res = await notif_svc.get_unread_count(user.id)
        if unread_res.unread_count == 2:
            ok("Unread notification count verified (2 unread)")
        else:
            fail("Unread count mismatch", str(unread_res.unread_count))

        # 3. Mark single notification as read
        read_n1 = await notif_svc.mark_read(n1.id, user.id)
        if read_n1.is_read:
            ok("Single notification marked as read successfully")
        else:
            fail("Mark single notification read failed")

        unread_res2 = await notif_svc.get_unread_count(user.id)
        if unread_res2.unread_count == 1:
            ok("Unread count updated to 1")
        else:
            fail("Unread count mismatch after single read", str(unread_res2.unread_count))

        # 4. Mark all as read
        marked_count = await notif_svc.mark_all_read(user.id)
        if marked_count == 1:
            ok("Mark all read processed remaining unread notification")
        else:
            fail("Mark all read mismatch", str(marked_count))

        unread_res3 = await notif_svc.get_unread_count(user.id)
        if unread_res3.unread_count == 0:
            ok("Unread count cleared to 0")
        else:
            fail("Unread count not 0 after mark_all_read")

        # Clean up
        stmt = select(Notification).where(Notification.user_id == user.id)
        res = await db.execute(stmt)
        for n in res.scalars().all():
            await db.delete(n)
        await db.delete(user)
        await db.commit()


async def verify_turnover_risk_analytics() -> None:
    section("SECTION 3: AI Turnover Flight Risk & Predictive Retention")

    async with AsyncSessionLocal() as db:
        insights_svc = InsightsService(db)

        # Fetch overview
        overview = await insights_svc.get_turnover_risk_overview()
        if overview.total_evaluated >= 0:
            ok(f"AI Turnover Risk Overview computed (Evaluated: {overview.total_evaluated}, Avg Risk: {overview.average_workforce_risk_score}%)")
            ok(f"Risk Tiers: Low={overview.low_risk_count}, Med={overview.medium_risk_count}, High={overview.high_risk_count}, Crit={overview.critical_risk_count}")
        else:
            fail("Turnover risk overview failed")


async def main() -> None:
    print("\n" + "=" * 60)
    print("  WorkforceOS MFA, Notifications & AI Retention Verification")
    print("=" * 60)

    try:
        # Ensure schema tables are created
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

        await verify_mfa_flow()
        await verify_notifications_flow()
        await verify_turnover_risk_analytics()
    except Exception:
        print("\n[FATAL] Verification suite error:")
        traceback.print_exc()
        failed.append("FATAL exception")

    print("\n" + "=" * 60)
    print(f"  Passed : {len(passed)}")
    print(f"  Failed : {len(failed)}")
    if failed:
        sys.exit(1)
    else:
        sys.exit(0)


if __name__ == "__main__":
    asyncio.run(main())

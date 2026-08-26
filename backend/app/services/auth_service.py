from __future__ import annotations

from uuid import UUID
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import (
    create_access_token,
    create_refresh_token,
    create_mfa_challenge_token,
    decode_token,
    generate_mfa_secret,
    get_totp_uri,
    verify_totp_code,
    get_password_hash,
    verify_password,
)
from app.models.user import User, UserRole
from app.models.audit_log import AuditLog
from app.schemas.auth import (
    UserLogin,
    UserRegister,
    MFASetupResponse,
    TokenResponse,
    TokenRefreshResponse,
)


class AuthService:
    """Handles user registration, authentication, MFA security, and token lifecycle."""

    def __init__(self, db_session: AsyncSession) -> None:
        self.db_session = db_session

    # ------------------------------------------------------------------
    # Registration
    # ------------------------------------------------------------------

    async def register(self, schema: UserRegister) -> tuple[User, str, str]:
        """Create a new user account and issue access + refresh tokens."""
        email_lower = schema.email.strip().lower()

        stmt = select(User).where(User.email == email_lower)
        result = await self.db_session.execute(stmt)
        existing = result.scalar_one_or_none()

        if existing:
            raise ValueError(
                f"A user with email '{email_lower}' is already registered."
            )

        user = User(
            email=email_lower,
            hashed_password=get_password_hash(schema.password),
            role=UserRole(schema.role),
            is_mfa_enabled=False,
        )

        self.db_session.add(user)
        await self.db_session.commit()
        await self.db_session.refresh(user)

        # Issue JWTs
        token_payload = {"sub": str(user.id), "role": user.role.value}
        access_token = create_access_token(data=token_payload)
        refresh_token = create_refresh_token(data={"sub": str(user.id)})

        return user, access_token, refresh_token

    # ------------------------------------------------------------------
    # Login & 2FA Challenge Flow
    # ------------------------------------------------------------------

    async def login(self, schema: UserLogin) -> TokenResponse:
        """Authenticate user by email + password.
        
        If MFA is enabled on the account, issues a temporary 5-minute MFA challenge token.
        Otherwise, issues complete access + refresh tokens.
        """
        email_lower = schema.username.strip().lower()

        stmt = select(User).where(
            User.email == email_lower,
            User.is_deleted == False,  # noqa: E712
        )
        result = await self.db_session.execute(stmt)
        user = result.scalar_one_or_none()

        if user is None or not verify_password(schema.password, user.hashed_password):
            raise ValueError("Invalid email or password.")

        if user.is_mfa_enabled:
            challenge_token = create_mfa_challenge_token(
                data={"sub": str(user.id), "email": user.email, "role": user.role.value}
            )
            return TokenResponse(
                mfa_required=True,
                mfa_token=challenge_token,
                token_type="bearer",
            )

        token_payload = {"sub": str(user.id), "role": user.role.value}
        access_token = create_access_token(data=token_payload)
        refresh_token = create_refresh_token(data={"sub": str(user.id)})

        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
            mfa_required=False,
        )

    async def verify_mfa_login(self, mfa_token: str, code: str) -> TokenResponse:
        """Verify 2FA TOTP code for a user holding a valid MFA challenge token."""
        try:
            payload = decode_token(mfa_token)
        except Exception:
            raise ValueError("MFA challenge token is invalid or has expired. Please log in again.")

        if payload.get("type") != "mfa_challenge":
            raise ValueError("Invalid token type for MFA verification.")

        user_id_str = payload.get("sub")
        if not user_id_str:
            raise ValueError("Invalid token payload.")

        user = await self.db_session.get(User, UUID(user_id_str))
        if not user or user.is_deleted or not user.is_mfa_enabled:
            raise ValueError("User not found or MFA is not active.")

        if not verify_totp_code(user.mfa_secret or "", code):
            raise ValueError("Invalid 6-digit verification code.")

        token_payload = {"sub": str(user.id), "role": user.role.value}
        access_token = create_access_token(data=token_payload)
        refresh_token = create_refresh_token(data={"sub": str(user.id)})

        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
            mfa_required=False,
        )

    # ------------------------------------------------------------------
    # MFA Management
    # ------------------------------------------------------------------

    async def setup_mfa(self, user_id: UUID) -> MFASetupResponse:
        """Generate a new base32 TOTP secret key and provisioning URI for QR code setup."""
        user = await self.db_session.get(User, user_id)
        if not user or user.is_deleted:
            raise ValueError("User not found.")

        secret = generate_mfa_secret()
        # Save secret in pending state (until enabled with valid code)
        user.mfa_secret = secret
        await self.db_session.commit()

        otpauth_url = get_totp_uri(secret=secret, email=user.email)
        return MFASetupResponse(secret=secret, otpauth_url=otpauth_url)

    async def enable_mfa(self, user_id: UUID, password: str, code: str) -> bool:
        """Verify password and 6-digit TOTP code, then permanently activate MFA for user."""
        user = await self.db_session.get(User, user_id)
        if not user or user.is_deleted:
            raise ValueError("User not found.")

        if not verify_password(password, user.hashed_password):
            raise ValueError("Invalid account password.")

        if not user.mfa_secret:
            raise ValueError("MFA setup was not initiated. Please run setup first.")

        if not verify_totp_code(user.mfa_secret, code):
            raise ValueError("Invalid 6-digit TOTP verification code.")

        user.is_mfa_enabled = True
        self.db_session.add(
            AuditLog(
                user_id=user.id,
                action="ENABLE_MFA",
                target_type="users",
                target_id=user.id,
                details={"status": "ENABLED"},
            )
        )
        await self.db_session.commit()
        return True

    async def disable_mfa(self, user_id: UUID, password: str, code: str) -> bool:
        """Verify password and code, then deactivate MFA."""
        user = await self.db_session.get(User, user_id)
        if not user or user.is_deleted:
            raise ValueError("User not found.")

        if not verify_password(password, user.hashed_password):
            raise ValueError("Invalid account password.")

        if not user.is_mfa_enabled:
            raise ValueError("MFA is not currently enabled on this account.")

        if not verify_totp_code(user.mfa_secret or "", code):
            raise ValueError("Invalid 6-digit TOTP verification code.")

        user.is_mfa_enabled = False
        user.mfa_secret = None
        self.db_session.add(
            AuditLog(
                user_id=user.id,
                action="DISABLE_MFA",
                target_type="users",
                target_id=user.id,
                details={"status": "DISABLED"},
            )
        )
        await self.db_session.commit()
        return True

    # ------------------------------------------------------------------
    # Refresh Token Rotation
    # ------------------------------------------------------------------

    async def rotate_refresh_token(self, refresh_token_str: str) -> TokenRefreshResponse:
        """Validate refresh token and issue a fresh access token + new rotated refresh token."""
        try:
            payload = decode_token(refresh_token_str)
        except Exception:
            raise ValueError("Refresh token is invalid or has expired.")

        if payload.get("type") != "refresh":
            raise ValueError("Invalid token type. Refresh token required.")

        user_id_str = payload.get("sub")
        if not user_id_str:
            raise ValueError("Invalid token payload.")

        user = await self.db_session.get(User, UUID(user_id_str))
        if not user or user.is_deleted:
            raise ValueError("User account is inactive or deleted.")

        token_payload = {"sub": str(user.id), "role": user.role.value}
        new_access_token = create_access_token(data=token_payload)
        new_refresh_token = create_refresh_token(data={"sub": str(user.id)})

        return TokenRefreshResponse(
            access_token=new_access_token,
            refresh_token=new_refresh_token,
            token_type="bearer",
        )


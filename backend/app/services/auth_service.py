"""
Authentication service layer.

Follows the same convention as EmployeeService / DepartmentService:
  - Receives an AsyncSession via __init__
  - Business logic + validation + DB interaction
  - Raises ValueError on domain errors (caught by router as 400/401)

Integrates with:
  - app.core.security   — password hashing, JWT creation
  - app.models.user      — User ORM model, UserRole enum
"""
from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import (
    create_access_token,
    get_password_hash,
    verify_password,
)
from app.models.user import User, UserRole
from app.schemas.auth import UserLogin, UserRegister


class AuthService:
    """Handles user registration and authentication."""

    def __init__(self, db_session: AsyncSession) -> None:
        self.db_session = db_session

    # ------------------------------------------------------------------
    # Registration
    # ------------------------------------------------------------------

    async def register(self, schema: UserRegister) -> tuple[User, str]:
        """Create a new user account.

        Returns:
            Tuple of (User instance, JWT access token).

        Raises:
            ValueError: If the email address is already registered.
        """
        # 1. Check for duplicate email (case-insensitive)
        email_lower = schema.email.strip().lower()

        stmt = select(User).where(User.email == email_lower)
        result = await self.db_session.execute(stmt)
        existing = result.scalar_one_or_none()

        if existing:
            raise ValueError(
                f"A user with email '{email_lower}' is already registered."
            )

        # 2. Create User record
        user = User(
            email=email_lower,
            hashed_password=get_password_hash(schema.password),
            role=UserRole(schema.role),
        )

        self.db_session.add(user)
        await self.db_session.commit()
        await self.db_session.refresh(user)

        # 3. Issue JWT so the user can authenticate immediately
        token = create_access_token(
            data={"sub": str(user.id), "role": user.role.value}
        )

        return user, token

    # ------------------------------------------------------------------
    # Login
    # ------------------------------------------------------------------

    async def login(self, schema: UserLogin) -> tuple[User, str]:
        """Authenticate an existing user by email + password.

        Returns:
            Tuple of (User instance, JWT access token).

        Raises:
            ValueError: If credentials are invalid or the account is soft-deleted.
        """
        email_lower = schema.username.strip().lower()

        # 1. Lookup user by email (excluding soft-deleted accounts)
        stmt = select(User).where(
            User.email == email_lower,
            User.is_deleted == False,  # noqa: E712 — SQLAlchemy filter
        )
        result = await self.db_session.execute(stmt)
        user = result.scalar_one_or_none()

        if user is None:
            # Generic error — do not reveal whether the email exists
            raise ValueError("Invalid email or password.")

        # 2. Verify password
        if not verify_password(schema.password, user.hashed_password):
            raise ValueError("Invalid email or password.")

        # 3. Issue JWT
        token = create_access_token(
            data={"sub": str(user.id), "role": user.role.value}
        )

        return user, token

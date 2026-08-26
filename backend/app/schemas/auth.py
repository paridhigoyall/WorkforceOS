"""
Pydantic schemas for authentication endpoints.

Follows the same conventions as department.py / employee.py:
 - Field(...) with descriptions
 - field_validator for input sanitisation
 - ConfigDict(from_attributes=True) on response models
"""
from __future__ import annotations

import re
from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator


# ---------------------------------------------------------------------------
# Request schemas
# ---------------------------------------------------------------------------

class UserRegister(BaseModel):
    """POST /auth/register — request body."""

    email: EmailStr = Field(
        ...,
        description="User email address (must be unique across the system)",
    )
    password: str = Field(
        ...,
        min_length=8,
        max_length=128,
        description="Plain-text password (min 8 characters)",
    )
    role: str = Field(
        "staff",
        description="User role: admin | hr | staff (defaults to staff)",
    )

    @field_validator("password")
    @classmethod
    def validate_password_strength(cls, value: str) -> str:
        """Enforce minimum complexity: at least one letter and one digit."""
        if not re.search(r"[A-Za-z]", value):
            raise ValueError("Password must contain at least one letter")
        if not re.search(r"\d", value):
            raise ValueError("Password must contain at least one digit")
        return value

    @field_validator("role")
    @classmethod
    def validate_role(cls, value: str) -> str:
        allowed = {"admin", "hr", "staff"}
        lower = value.strip().lower()
        if lower not in allowed:
            raise ValueError(f"Role must be one of: {', '.join(sorted(allowed))}")
        return lower


class UserLogin(BaseModel):
    """POST /auth/login — request body.

    Uses ``username`` (not ``email``) to be compatible with
    OAuth2PasswordRequestForm which FastAPI's Swagger "Authorize"
    button sends as ``username``.
    """

    username: str = Field(
        ...,
        description="User email address (named 'username' for OAuth2 compatibility)",
    )
    password: str = Field(
        ...,
        description="Plain-text password",
    )


# ---------------------------------------------------------------------------
# Response & MFA schemas
# ---------------------------------------------------------------------------

class TokenResponse(BaseModel):
    """Returned on successful login."""

    access_token: str | None = Field(default=None, description="JWT access token")
    refresh_token: str | None = Field(default=None, description="JWT refresh token")
    token_type: str = Field(default="bearer", description="Token type (always 'bearer')")
    mfa_required: bool = Field(default=False, description="True if TOTP code must be verified")
    mfa_token: str | None = Field(default=None, description="Temporary challenge token for MFA validation")


class TokenRefreshRequest(BaseModel):
    """POST /auth/refresh — request body."""

    refresh_token: str = Field(..., description="Valid JWT refresh token")


class TokenRefreshResponse(BaseModel):
    """POST /auth/refresh — response body."""

    access_token: str = Field(..., description="New JWT access token")
    refresh_token: str = Field(..., description="New rotated JWT refresh token")
    token_type: str = Field(default="bearer")


class MFASetupResponse(BaseModel):
    """POST /auth/mfa/setup — response body."""

    secret: str = Field(..., description="Base32 TOTP secret key for manual entry")
    otpauth_url: str = Field(..., description="otpauth:// provisioning URI for QR code generators")


class MFAVerifyRequest(BaseModel):
    """POST /auth/mfa/verify — 2FA login verification."""

    mfa_token: str = Field(..., description="Temporary challenge token from initial login step")
    code: str = Field(..., min_length=6, max_length=6, description="6-digit TOTP code")


class MFAToggleRequest(BaseModel):
    """POST /auth/mfa/enable or disable — request body."""

    password: str = Field(..., description="Account password for confirmation")
    code: str = Field(..., min_length=6, max_length=6, description="6-digit TOTP verification code")


class UserResponse(BaseModel):
    """Public-facing user representation (no password hash exposed)."""

    id: UUID
    email: str
    role: str
    is_mfa_enabled: bool = False
    is_deleted: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class RegisterResponse(BaseModel):
    """Returned on successful registration — user + token for immediate use."""

    user: UserResponse
    access_token: str = Field(..., description="JWT access token for immediate use")
    refresh_token: str | None = Field(default=None, description="JWT refresh token")
    token_type: str = Field(default="bearer")


from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies.auth import get_current_user
from app.core.database import get_db
from app.models.user import User
from app.schemas.auth import (
    RegisterResponse,
    TokenResponse,
    TokenRefreshRequest,
    TokenRefreshResponse,
    MFASetupResponse,
    MFAVerifyRequest,
    MFAToggleRequest,
    UserRegister,
    UserResponse,
)
from app.services.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["Authentication"])


# ---------------------------------------------------------------------------
# POST /auth/register
# ---------------------------------------------------------------------------

@router.post(
    "/register",
    response_model=RegisterResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user",
    description="Creates a new user account and returns access and refresh tokens.",
)
async def register(
    schema: UserRegister,
    db: AsyncSession = Depends(get_db),
):
    service = AuthService(db)
    try:
        user, access_token, refresh_token = await service.register(schema)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    return RegisterResponse(
        user=UserResponse.model_validate(user),
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
    )


# ---------------------------------------------------------------------------
# POST /auth/login
# ---------------------------------------------------------------------------

@router.post(
    "/login",
    response_model=TokenResponse,
    summary="Login and obtain access token or MFA challenge",
    description=(
        "Authenticate with email + password. Returns JWT access and refresh tokens, "
        "or an MFA challenge token if 2FA is active."
    ),
)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db),
):
    service = AuthService(db)
    try:
        token_response = await service.login(
            type(
                "LoginPayload",
                (),
                {"username": form_data.username, "password": form_data.password},
            )()
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
            headers={"WWW-Authenticate": "Bearer"},
        )
    return token_response


# ---------------------------------------------------------------------------
# POST /auth/mfa/verify
# ---------------------------------------------------------------------------

@router.post(
    "/mfa/verify",
    response_model=TokenResponse,
    summary="Complete 2FA login challenge",
    description="Validate 6-digit TOTP code against the temporary challenge token.",
)
async def verify_mfa_login(
    payload: MFAVerifyRequest,
    db: AsyncSession = Depends(get_db),
):
    service = AuthService(db)
    try:
        return await service.verify_mfa_login(payload.mfa_token, payload.code)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
        )


# ---------------------------------------------------------------------------
# POST /auth/mfa/setup
# ---------------------------------------------------------------------------

@router.post(
    "/mfa/setup",
    response_model=MFASetupResponse,
    summary="Generate TOTP secret for MFA enrollment",
    description="Generates a base32 secret and otpauth URI for Google Authenticator QR setup.",
)
async def setup_mfa(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = AuthService(db)
    try:
        return await service.setup_mfa(current_user.id)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


# ---------------------------------------------------------------------------
# POST /auth/mfa/enable
# ---------------------------------------------------------------------------

@router.post(
    "/mfa/enable",
    status_code=status.HTTP_200_OK,
    summary="Enable MFA on user account",
    description="Confirms password and 6-digit TOTP code to permanently activate 2FA.",
)
async def enable_mfa(
    payload: MFAToggleRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = AuthService(db)
    try:
        await service.enable_mfa(current_user.id, payload.password, payload.code)
        return {"status": "success", "message": "Multi-factor authentication enabled."}
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


# ---------------------------------------------------------------------------
# POST /auth/mfa/disable
# ---------------------------------------------------------------------------

@router.post(
    "/mfa/disable",
    status_code=status.HTTP_200_OK,
    summary="Disable MFA on user account",
    description="Confirms password and 6-digit TOTP code to deactivate 2FA.",
)
async def disable_mfa(
    payload: MFAToggleRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = AuthService(db)
    try:
        await service.disable_mfa(current_user.id, payload.password, payload.code)
        return {"status": "success", "message": "Multi-factor authentication disabled."}
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


# ---------------------------------------------------------------------------
# POST /auth/refresh
# ---------------------------------------------------------------------------

@router.post(
    "/refresh",
    response_model=TokenRefreshResponse,
    summary="Rotate refresh token and get fresh access token",
    description="Validates the supplied refresh token and issues a new access + rotated refresh token.",
)
async def refresh_token(
    payload: TokenRefreshRequest,
    db: AsyncSession = Depends(get_db),
):
    service = AuthService(db)
    try:
        return await service.rotate_refresh_token(payload.refresh_token)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
        )


# ---------------------------------------------------------------------------
# GET /auth/me
# ---------------------------------------------------------------------------

@router.get(
    "/me",
    response_model=UserResponse,
    summary="Get current user profile",
    description="Returns the currently authenticated user details including MFA status.",
)
async def get_me(
    current_user: User = Depends(get_current_user),
):
    return UserResponse.model_validate(current_user)

